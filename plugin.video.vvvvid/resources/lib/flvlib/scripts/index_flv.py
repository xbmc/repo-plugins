import os
import sys
import shutil
import logging
import tempfile

from optparse import OptionParser

from flvlib import __versionstr__
from flvlib.constants import TAG_TYPE_AUDIO, TAG_TYPE_VIDEO, TAG_TYPE_SCRIPT
from flvlib.constants import FRAME_TYPE_KEYFRAME
from flvlib.astypes import MalformedFLV, FLVObject
from flvlib.tags import FLV, EndOfFile, AudioTag, VideoTag, ScriptTag
from flvlib.tags import create_script_tag, create_flv_header
from flvlib.helpers import force_remove

log = logging.getLogger('flvlib.index-flv')


class IndexingAudioTag(AudioTag):

    SEEKPOINT_DENSITY = 10

    def __init__(self, parent_flv, f):
        AudioTag.__init__(self, parent_flv, f)

    def parse(self):
        parent = self.parent_flv
        AudioTag.parse(self)

        if not parent.first_media_tag_offset:
            parent.first_media_tag_offset = self.offset


        # If the FLV has video, we're done. No need to store audio seekpoint
        # information anymore.
        if not parent.no_video:
            return

        # We haven't seen any video tag yet. Store every SEEKPOINT_DENSITY tag
        # offset and timestamp.
        parent.audio_tag_number += 1
        if (parent.audio_tag_number % self.SEEKPOINT_DENSITY == 0):
            parent.audio_seekpoints.filepositions.append(self.offset)
            parent.audio_seekpoints.times.append(self.timestamp / 1000.0)


class IndexingVideoTag(VideoTag):

    def parse(self):
        parent = self.parent_flv
        VideoTag.parse(self)

        parent.no_video = False

        if not parent.first_media_tag_offset:
            parent.first_media_tag_offset = self.offset

        if self.frame_type == FRAME_TYPE_KEYFRAME:
            parent.keyframes.filepositions.append(self.offset)
            parent.keyframes.times.append(self.timestamp / 1000.0)


class IndexingScriptTag(ScriptTag):

    def parse(self):
        parent = self.parent_flv
        ScriptTag.parse(self)

        if self.name == 'onMetaData':
            parent.metadata = self.variable
            parent.metadata_tag_start = self.offset
            parent.metadata_tag_end = self.f.tell()


tag_to_class = {
    TAG_TYPE_AUDIO: IndexingAudioTag,
    TAG_TYPE_VIDEO: IndexingVideoTag,
    TAG_TYPE_SCRIPT: IndexingScriptTag
}


class IndexingFLV(FLV):

    def __init__(self, f):
        FLV.__init__(self, f)
        self.metadata = None
        self.keyframes = FLVObject()
        self.keyframes.filepositions = []
        self.keyframes.times = []
        self.no_video = True

        # If the FLV file has no video, there are no keyframes. We want to put
        # some info in the metadata anyway -- Flash players use keyframe
        # information as a seek table. In audio-only FLV files you can usually
        # seek to the beginning of any tag (this is not entirely true for AAC).
        # Most players still work if you just provide "keyframe" info that's
        # really a table of every Nth audio tag, even with AAC.
        # Because of that, until we see a video tag we make every Nth
        # IndexingAudioTag store its offset and timestamp.
        self.audio_tag_number = 0
        self.audio_seekpoints = FLVObject()
        self.audio_seekpoints.filepositions = []
        self.audio_seekpoints.times = []

        self.metadata_tag_start = None
        self.metadata_tag_end = None
        self.first_media_tag_offset = None

    def tag_type_to_class(self, tag_type):
        try:
            return tag_to_class[tag_type]
        except KeyError:
            raise MalformedFLV("Invalid tag type: %d", tag_type)


def filepositions_difference(metadata, original_metadata_size):
    test_payload = create_script_tag('onMetaData', metadata)
    payload_size = len(test_payload)
    difference = payload_size - original_metadata_size
    return test_payload, difference


def retimestamp_and_index_file(inpath, outpath=None, retimestamp=None):

    # no retimestamping needed
    if retimestamp is None:

        return index_file(inpath, outpath)

    # retimestamp the input in place and index
    elif retimestamp == 'inplace':
        from flvlib.scripts.retimestamp_flv import retimestamp_file_inplace

        log.debug("Retimestamping file `%s' in place", inpath)

        # retimestamp the file inplace
        if not retimestamp_file_inplace(inpath):
            log.error("Failed to retimestamp `%s' in place", inpath)
            return False

        return index_file(inpath, outpath)

    # retimestamp the input into a temporary file
    elif retimestamp == 'atomic':
        from flvlib.scripts.retimestamp_flv import retimestamp_file_atomically

        log.debug("Retimestamping file `%s' atomically", inpath)

        try:
            fd, temppath = tempfile.mkstemp()
            os.close(fd)
            # preserve the permission bits
            shutil.copymode(inpath, temppath)
        except EnvironmentError, (errno, strerror):
            log.error("Failed to create temporary file: %s", strerror)
            return False

        if not retimestamp_file_atomically(inpath, temppath):
            log.error("Failed to retimestamp `%s' atomically", inpath)
            # remove the temporary files
            force_remove(temppath)
            return False

        # index the temporary file
        if not index_file(temppath, outpath):
            force_remove(temppath)
            return False

        if not outpath:
            # If we were not writing directly to the output file
            # we need to overwrite the original
            try:
                shutil.move(temppath, inpath)
            except EnvironmentError, (errno, strerror):
                log.error("Failed to overwrite the original file with the "
                          "retimestamped and indexed version: %s", strerror)
                return False
        else:
            # if we were writing directly to the output file we need to remove
            # the retimestamped temporary file
            force_remove(temppath)

        return True


def index_file(inpath, outpath=None):
    out_text = (outpath and ("into file `%s'" % outpath)) or "and overwriting"
    log.debug("Indexing file `%s' %s", inpath, out_text)

    try:
        f = open(inpath, 'rb')
    except IOError, (errno, strerror):
        log.error("Failed to open `%s': %s", inpath, strerror)
        return False

    flv = IndexingFLV(f)
    tag_iterator = flv.iter_tags()
    last_tag = None

    try:
        while True:
            tag = tag_iterator.next()
            # some buggy software, like gstreamer's flvmux, puts a metadata tag
            # at the end of the file with timestamp 0, and we don't want to
            # base our duration computation on that
            if tag.timestamp != 0:
                last_tag = tag
    except MalformedFLV, e:
        message = e[0] % e[1:]
        log.error("The file `%s' is not a valid FLV file: %s", inpath, message)
        return False
    except EndOfFile:
        log.error("Unexpected end of file on file `%s'", inpath)
        return False
    except StopIteration:
        pass

    if not flv.first_media_tag_offset:
        log.error("The file `%s' does not have any media content", inpath)
        return False

    if not last_tag:
        log.error("The file `%s' does not have any content with a "
                  "non-zero timestamp", inpath)
        return False

    metadata = flv.metadata or {}

    if flv.metadata_tag_start:
        original_metadata_size = flv.metadata_tag_end - flv.metadata_tag_start
    else:
        log.debug("The file `%s' has no metadata", inpath)
        original_metadata_size = 0

    keyframes = flv.keyframes

    if flv.no_video:
        log.info("The file `%s' has no video, using audio seekpoints info",
                 inpath)
        keyframes = flv.audio_seekpoints

    duration = metadata.get('duration')
    if not duration:
        # A duration of 0 is nonsensical, yet some tools put it like that. In
        # that case (or when there is no such field) update the duration value.
        duration = last_tag.timestamp / 1000.0

    metadata['duration'] = duration
    metadata['keyframes'] = keyframes
    metadata['metadatacreator'] = 'flvlib %s' % __versionstr__

    # we're going to write new metadata, so we need to shift the
    # filepositions by the amount of bytes that we're going to add to
    # the metadata tag
    test_payload, difference = filepositions_difference(metadata,
                                                        original_metadata_size)

    if difference:
        new_filepositions = [pos + difference
                             for pos in keyframes.filepositions]
        metadata['keyframes'].filepositions = new_filepositions
        payload = create_script_tag('onMetaData', metadata)
    else:
        log.debug("The file `%s' metadata size did not change.", inpath)
        payload = test_payload

    if outpath:
        try:
            fo = open(outpath, 'wb')
        except IOError, (errno, strerror):
            log.error("Failed to open `%s': %s", outpath, strerror)
            return False
    else:
        try:
            fd, temppath = tempfile.mkstemp()
            # preserve the permission bits
            shutil.copymode(inpath, temppath)
            fo = os.fdopen(fd, 'wb')
        except EnvironmentError, (errno, strerror):
            log.error("Failed to create temporary file: %s", strerror)
            return False

    log.debug("Creating the output file")

    try:
        fo.write(create_flv_header(has_audio=flv.has_audio,
                                   has_video=flv.has_video))
        fo.write(payload)
        f.seek(flv.first_media_tag_offset)
        shutil.copyfileobj(f, fo)
    except IOError, (errno, strerror):
        log.error("Failed to create the indexed file: %s", strerror)
        if not outpath:
            # remove the temporary file
            force_remove(temppath)
        return False

    f.close()
    fo.close()

    if not outpath:
        # If we were not writing directly to the output file
        # we need to overwrite the original
        try:
            shutil.move(temppath, inpath)
        except EnvironmentError, (errno, strerror):
            log.error("Failed to overwrite the original file "
                      "with the indexed version: %s", strerror)
            return False

    return True


def process_options():
    usage = "%prog [-U] file [outfile|file2 file3 ...]"
    description = ("Finds keyframe timestamps and file offsets "
                   "in FLV files and updates the onMetaData "
                   "script tag with that information. "
                   "With the -U (update) option operates on all parameters, "
                   "overwriting the original file. Without the -U "
                   "option accepts one input and one output file path.")
    version = "%%prog flvlib %s" % __versionstr__
    parser = OptionParser(usage=usage, description=description,
                          version=version)
    parser.add_option("-U", "--update", action="store_true",
                      help=("update mode, overwrites the given files "
                            "instead of writing to outfile"))
    parser.add_option("-r", "--retimestamp", action="store_true",
                      help=("rewrite timestamps in the files before indexing, "
                            "identical to running retimestamp-flv first"))
    parser.add_option("-R", "--retimestamp-inplace", action="store_true",
                      help=("same as -r but avoid creating temporary files at "
                            "the risk of corrupting the input files in case "
                            "of errors"))
    parser.add_option("-v", "--verbose", action="count",
                      default=0, dest="verbosity",
                      help="be more verbose, each -v increases verbosity")
    options, args = parser.parse_args(sys.argv)

    if len(args) < 2:
        parser.error("You have to provide at least one file path")

    if not options.update and len(args) != 3:
        parser.error("You need to provide one infile and one outfile "
                     "when not using the update mode")

    if options.retimestamp and options.retimestamp_inplace:
        parser.error("You cannot provide both -r and -R")

    if options.verbosity > 3:
        options.verbosity = 3

    log.setLevel({0: logging.ERROR, 1: logging.WARNING,
                  2: logging.INFO, 3: logging.DEBUG}[options.verbosity])

    return options, args


def index_files():
    options, args = process_options()

    clean_run = True

    retimestamp_mode = None
    if options.retimestamp:
        retimestamp_mode = 'atomic'
    elif options.retimestamp_inplace:
        retimestamp_mode = 'inplace'

    if not options.update:
        clean_run = retimestamp_and_index_file(args[1], args[2],
                                               retimestamp=retimestamp_mode)
    else:
        for filename in args[1:]:
            if not retimestamp_and_index_file(filename,
                                              retimestamp=retimestamp_mode):
                clean_run = False

    return clean_run


def main():
    try:
        outcome = index_files()
    except KeyboardInterrupt:
        # give the right exit status, 128 + signal number
        # signal.SIGINT = 2
        sys.exit(128 + 2)
    except EnvironmentError, (errno, strerror):
        try:
            print >>sys.stderr, strerror
        except StandardError:
            pass
        sys.exit(2)

    if outcome:
        sys.exit(0)
    else:
        sys.exit(1)
