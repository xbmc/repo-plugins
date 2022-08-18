# -*- coding: utf-8 -*-

# Copyright (c) 2016-2020 Wintermute0110 <wintermute0110@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; version 2 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.

# Advanced MAME Launcher MAME specific stuff.

# --- AEL packages ---
from .constants import *
from .utils import *
from .misc import *
from .db import *
from .filters import *
from .mame_misc import *

# --- Kodi modules ---
import xbmcgui

# --- Python standard library ---
import binascii
import struct
import xml.etree.ElementTree as ET
import zipfile as z

# -------------------------------------------------------------------------------------------------
# Data structures
# -------------------------------------------------------------------------------------------------
# Substitute notable drivers with a proper name
# Drivers are located in https://github.com/mamedev/mame/blob/master/src/mame/drivers/<driver_name>.cpp
mame_driver_better_name_dic = {
    # --- Atari ---
    'atari_s1.cpp' : 'Atari Generation/System 1',
    'atari_s2.cpp' : 'Atari Generation/System 2 and 3',
    'atarifb.cpp'  : 'Atari Football hardware',
    'atarittl.cpp' : 'Atari / Kee Games Driver',
    'asteroid.cpp' : 'Atari Asteroids hardware',
    'atetris.cpp'  : 'Atari Tetris hardware',
    'avalnche.cpp' : 'Atari Avalanche hardware',
    'bzone.cpp'    : 'Atari Battlezone hardware',
    'bwidow.cpp'   : 'Atari Black Widow hardware',
    'boxer.cpp'    : 'Atari Boxer (prototype) driver',
    'canyon.cpp'   : 'Atari Canyon Bomber hardware',
    'cball.cpp'    : 'Atari Cannonball (prototype) driver',
    'ccastles.cpp' : 'Atari Crystal Castles hardware',
    'centiped.cpp' : 'Atari Centipede hardware',
    'cloak.cpp'    : 'Atari Cloak & Dagger hardware',
    'destroyr.cpp' : 'Atari Destroyer driver',
    'mhavoc.cpp'   : 'Atari Major Havoc hardware',
    'mgolf.cpp'    : 'Atari Mini Golf (prototype) driver',
    'pong.cpp'     : 'Atari Pong hardware',

    # --- Capcom ---
    '1942.cpp'   : 'Capcom 1942',
    '1943.cpp'   : 'Capcom 1943: The Battle of Midway',
    'capcom.cpp' : 'Capcom A0015405',
    'gng.cpp'    : "Capcom Ghosts'n Goblins",
    'cps1.cpp'   : 'Capcom Play System 1',
    'cps2.cpp'   : 'Capcom Play System 2',
    'cps3.cpp'   : 'Capcom Play System 3',

    # --- Konami ---
    '88games.cpp'   : 'Konami 88 Games',
    'ajax.cpp'      : 'Konami GX770',
    'aliens.cpp'    : 'Konami Aliens',
    'asterix.cpp'   : 'Konami Asterix',
    'konamigv.cpp'  : 'Konami GV System (PSX Hardware)',
    'konblands.cpp' : 'Konami GX455 - Konami Badlands',
    'konamigx.cpp'  : 'Konami System GX',
    'konamim2.cpp'  : 'Konami M2 Hardware',

    # --- Midway ---
    'midtunit.cpp' : 'Midway T-unit system',
    'midvunit.cpp' : 'Midway V-Unit games',
    'midwunit.cpp' : 'Midway Wolf-unit system',
    'midxunit.cpp' : 'Midway X-unit system',
    'midyunit.cpp' : 'Williams/Midway Y/Z-unit system',
    'midzeus.cpp'  : 'Midway Zeus games',

    # --- Namco ---
    'galaxian.cpp' : 'Namco Galaxian-derived hardware',
    'namcops2.cpp' : 'Namco System 246 / System 256 (Sony PS2 based)',

    # --- SNK ---
    'neodriv.hxx' : 'SNK NeoGeo AES',
    'neogeo.cpp'  : 'SNK NeoGeo MVS',

    # --- Misc important drivers (important enough to have a fancy name!) ---
    'seta.cpp' : 'Seta Hardware',

    # --- SEGA ---
    # Lesser known boards
    'segajw.cpp'    : 'SEGA GOLDEN POKER SERIES',
    'segam1.cpp'    : 'SEGA M1 hardware',
    'segaufo.cpp'   : 'SEGA UFO Catcher, Z80 type hardware',
    # Boards listed in wikipedia
    # Sega Z80 board is included in galaxian.cpp
    'vicdual.cpp'   : 'SEGA VIC Dual Game board',
    'segag80r.cpp'  : 'SEGA G-80 raster hardware',
    'segag80v.cpp'  : 'SEGA G-80 vector hardware',
    'zaxxon.cpp'    : 'SEGA Zaxxon hardware',
    'segald.cpp'    : 'SEGA LaserDisc Hardware',
    'system1.cpp'   : 'SEGA System1 / System 2',
    'segac2.cpp'    : 'SEGA System C (System 14)',
    'segae.cpp'     : 'SEGA System E',
    'segas16a.cpp'  : 'SEGA System 16A',
    'segas16b.cpp'  : 'SEGA System 16B',
    'system16.cpp'  : 'SEGA System 16 / 18 bootlegs',
    'segas24.cpp'   : 'SEGA System 24',
    'segas18.cpp'   : 'SEGA System 18',
    'kyugo.cpp'     : 'SEGA Kyugo Hardware',
    'segahang.cpp'  : 'SEGA Hang On hardware', # AKA Sega Space Harrier
    'segaorun.cpp'  : 'SEGA Out Run hardware',
    'segaxbd.cpp'   : 'SEGA X-board',
    'segaybd.cpp'   : 'SEGA Y-board',
    'segas32.cpp'   : 'SEGA System 32',
    'model1.cpp'    : 'SEGA Model 1',
    'model2.cpp'    : 'SEGA Model 2',
    'model3.cpp'    : 'SEGA Model 3',
    'stv.cpp'       : 'SEGA ST-V hardware',
    'naomi.cpp'     : 'SEGA Naomi / Naomi 2 / Atomiswave',
    'segasp.cpp'    : 'SEGA System SP (Spider)', # Naomi derived
    'chihiro.cpp'   : 'SEGA Chihiro (Xbox-based)',
    'triforce.cpp'  : 'SEGA Triforce Hardware',
    'lindbergh.cpp' : 'SEGA Lindbergh',

    # --- Taito ---
    # Ordered alphabetically
    'taito_b.cpp'  : 'Taito B System',
    'taito_f2.cpp' : 'Taito F2 System',
    'taito_f3.cpp' : 'Taito F3 System',
    'taito_h.cpp'  : 'Taito H system',
    'taito_l.cpp'  : 'Taito L System',
    'taito_o.cpp'  : 'Taito O system (Gambling)',
    'taito_x.cpp'  : 'Taito X system',
    'taito_z.cpp'  : 'Taito Z System (twin 68K with optional Z80)',
    'taitoair.cpp' : 'Taito Air System',
    'taitogn.cpp'  : 'Taito GNET Motherboard',
    'taitojc.cpp'  : 'Taito JC System',
    'taitopjc.cpp' : 'Taito Power-JC System',
    'taitosj.cpp'  : 'Taito SJ system',
    'taitottl.cpp' : 'Taito Discrete Hardware Games',
    'taitotz.cpp'  : 'Taito Type-Zero hardware',
    'taitowlf.cpp' : 'Taito Wolf System',

    # --- SONY ---
    'zn.cpp' : 'Sony ZN1/ZN2 (Arcade PSX)',
}

# Some Software Lists don't follow the convention of adding the company name at the beginning.
# I will try to create pull requests to fix theses and if the PRs are not accepted then
# SL names will be changed using the data here.
# Develop a test script to check wheter this substitutsion are used or not.
SL_better_name_dic = {
    'Amiga AGA disk images' : 'Commodore Amiga AGA disk images',
    'Amiga CD-32 CD-ROMs' : 'Commodore Amiga CD-32 CD-ROMs',
    'Amiga CDTV CD-ROMs' : 'Commodore Amiga CDTV CD-ROMs',
    'Amiga ECS disk images' : 'Commodore Amiga ECS disk images',
    'Amiga OCS disk images' : 'Commodore Amiga OCS disk images',
    'CC-40 cartridges' : 'Texas Instruments CC-40 cartridges',
    'CD-i CD-ROMs' : 'Philips/Sony CD-i CD-ROMs',
    'COMX-35 diskettes' : 'COMX COMX-35 diskettes',
    'EPSON PX-4 ROM capsules' : 'Epson PX-4 ROM capsules',
    'EPSON PX-8 ROM capsules' : 'Epson PX-8 ROM capsules',
    'IQ-151 cartridges' : 'ZPA Nový Bor IQ-151 cartridges',
    'IQ-151 disk images' : 'ZPA Nový Bor IQ-151 disk images',
    'Mac Harddisks' : 'Apple Mac Harddisks',
    'Macintosh 400K/800K Disk images' : 'Apple Macintosh 400K/800K Disk images',
    'Macintosh High Density Disk images' : 'Apple Macintosh High Density Disk images',
    'MC-1502 disk images' : 'Elektronika MC-1502 disk images',
    'MD-2 disk images' : 'Morrow Micro Decision MD-2 disk images',
    'Mega CD (Euro) CD-ROMs' : 'Sega Mega CD (Euro) CD-ROMs',
    'Mega CD (Jpn) CD-ROMs' : 'Sega Mega CD (Jpn) CD-ROMs',
    'MZ-2000 cassettes' : 'Sharp MZ-2000 cassettes',
    'MZ-2000 disk images' : 'Sharp MZ-2000 disk images',
    'MZ-2500 disk images' : 'Sharp MZ-2500 disk images',
    'Pippin CD-ROMs' : 'Apple/Bandai Pippin CD-ROMs',
    'Pippin disk images' : 'Apple/Bandai Pippin disk images',
    'SEGA Computer 3000 cartridges' : 'Sega Computer 3000 cartridges',
    'SEGA Computer 3000 cassettes' : 'Sega Computer 3000 cassettes',
    'Z88 ROM cartridges' : 'Cambridge Computer Z88 ROM cartridges',
    'ZX80 cassettes' : 'Sinclair ZX80 cassettes',
    'ZX81 cassettes' : 'Sinclair ZX81 cassettes',
    'ZX Spectrum +3 disk images' : 'Sinclair ZX Spectrum +3 disk images',
    'ZX Spectrum Beta Disc / TR-DOS disk images' : 'Sinclair ZX Spectrum Beta Disc / TR-DOS disk images',
}

#
# Numerical MAME version. Allows for comparisons like ver_mame >= MAME_VERSION_0190
# Support MAME versions higher than 0.53 August 12th 2001.
# See header of MAMEINFO.dat for a list of all MAME versions.
#
# M.mmm.Xbb
# |   | | |-> Beta flag 0, 1, ..., 99
# |   | |---> Release kind flag
# |   |       5 for non-beta, non-alpha, non RC versions.
# |   |       2 for RC versions
# |   |       1 for beta versions
# |   |       0 for alpha versions
# |   |-----> Minor version 0, 1, ..., 999
# |---------> Major version 0, ..., infinity
#
# See https://retropie.org.uk/docs/MAME/
# See https://www.mamedev.org/oldrel.html
#
# Examples:
#   '0.37b5'  ->  37105  (mame4all-pi, lr-mame2000 released 27 Jul 2000)
#   '0.37b16' ->  37116  (Last unconsistent MAME version, released 02 Jul 2001)
#   '0.53'    ->  53500  (MAME versioning is consistent from this release, released 12 Aug 2001)
#   '0.78'    ->  78500  (lr-mame2003, lr-mame2003-plus)
#   '0.139'   -> 139500  (lr-mame2010)
#   '0.160'   -> 160500  (lr-mame2015)
#   '0.174'   -> 174500  (lr-mame2016)
#   '0.206'   -> 206500
#
# mame_version_raw examples:
#   a) '0.194 (mame0194)' from '<mame build="0.194 (mame0194)" debug="no" mameconfig="10">'
#
# re.search() returns a MatchObject https://docs.python.org/2/library/re.html#re.MatchObject
def mame_get_numerical_version(mame_version_str):
    log_debug('mame_get_numerical_version() mame_version_str = "{}"'.format(mame_version_str))
    mame_version_int = 0
    # Search for old version scheme x.yyybzz
    m_obj_old = re.search('^(\d+)\.(\d+)b(\d+)', mame_version_str)
    # Search for modern, consistent versioning system x.yyy
    m_obj_modern = re.search('^(\d+)\.(\d+)', mame_version_str)
    if m_obj_old:
        major = int(m_obj_old.group(1))
        minor = int(m_obj_old.group(2))
        beta  = int(m_obj_old.group(3))
        release_flag = 1
        # log_debug('mame_get_numerical_version() major = {}'.format(major))
        # log_debug('mame_get_numerical_version() minor = {}'.format(minor))
        # log_debug('mame_get_numerical_version() beta  = {}'.format(beta))
        mame_version_int = major * 1000000 + minor * 1000 + release_flag * 100 + beta
    elif m_obj_modern:
        major = int(m_obj_modern.group(1))
        minor = int(m_obj_modern.group(2))
        release_flag = 5
        # log_debug('mame_get_numerical_version() major = {}'.format(major))
        # log_debug('mame_get_numerical_version() minor = {}'.format(minor))
        mame_version_int = major * 1000000 + minor * 1000 + release_flag * 100
    else:
        t = 'MAME version "{}" cannot be parsed.'.format(mame_version_str)
        log_error(t)
        raise TypeError(t)
    log_debug('mame_get_numerical_version() mame_version_int = {}'.format(mame_version_int))

    return mame_version_int

# Returns a string like '0.224 (mame0224)'.
def mame_get_MAME_exe_version(cfg, mame_prog_FN):
    (mame_dir, mame_exec) = os.path.split(mame_prog_FN.getPath())
    log_info('mame_get_MAME_exe_version() mame_prog_FN "{}"'.format(mame_prog_FN.getPath()))
    # log_info('mame_get_MAME_exe_version() mame_dir     "{}"'.format(mame_dir))
    # log_info('mame_get_MAME_exe_version() mame_exec    "{}"'.format(mame_exec))
    stdout_f = cfg.MAME_STDOUT_VER_PATH.getPath()
    err_f = cfg.MAME_STDERR_VER_PATH.getPath()
    with io.open(stdout_f, 'wb') as out, io.open(err_f, 'wb') as err:
        p = subprocess.Popen([mame_prog_FN.getPath(), '-version'], stdout = out, stderr = err, cwd = mame_dir)
        p.wait()

    # Read MAME version.
    lines = utils_load_file_to_slist(cfg.MAME_STDOUT_VER_PATH.getPath())
    # log_debug('mame_get_MAME_exe_version() Number of lines {}'.format(len(lines)))
    version_str = lines[0]
    # version_str = ''
    # for line in lines:
    #     m = re.search('^([0-9\.]+?) \(([a-z0-9]+?)\)$', line.strip())
    #     if m:
    #         version_str = m.group(1)
    #         break
    # log_debug('mame_get_MAME_exe_version() Returning "{}"'.format(version_str))

    return version_str

# Counts MAME machines in MAME XML file.
def mame_count_MAME_machines(XML_path_FN):
    log_debug('mame_count_MAME_machines_modern() BEGIN...')
    log_debug('XML "{}"'.format(XML_path_FN.getPath()))
    num_machines_modern = 0
    num_machines_legacy = 0
    with io.open(XML_path_FN.getPath(), 'rt', encoding = 'utf-8') as f:
        for line in f:
            if line.find('<machine name=') > 0:
                num_machines_modern += 1
                continue
            if line.find('<game name=') > 0:
                num_machines_legacy += 1
                continue
    if num_machines_modern and num_machines_legacy:
        log_error('num_machines_modern = {}'.format(num_machines_modern))
        log_error('num_machines_legacy = {}'.format(num_machines_legacy))
        log_error('Both cannot be > 0!')
        raise TypeError
    num_machines = num_machines_modern if num_machines_modern > num_machines_legacy else num_machines_legacy

    return num_machines

# 1) Extracts MAME XML.
# 2) Counts number of MAME machines.
# 3) Gets MAME version from the XML file.
# 4) Creates MAME XML control file.
def mame_extract_MAME_XML(cfg, st_dic):
    pDialog = KodiProgressDialog()

    # Extract XML from MAME executable.
    mame_prog_FN = FileName(cfg.settings['mame_prog'])
    (mame_dir, mame_exec) = os.path.split(mame_prog_FN.getPath())
    log_info('mame_extract_MAME_XML() mame_prog_FN "{}"'.format(mame_prog_FN.getPath()))
    log_info('mame_extract_MAME_XML() Saving XML   "{}"'.format(cfg.MAME_XML_PATH.getPath()))
    log_info('mame_extract_MAME_XML() mame_dir     "{}"'.format(mame_dir))
    log_info('mame_extract_MAME_XML() mame_exec    "{}"'.format(mame_exec))
    pDialog.startProgress('Extracting MAME XML database. Progress bar is not accurate.')
    XML_path_FN = cfg.MAME_XML_PATH
    with io.open(XML_path_FN.getPath(), 'wb') as out, io.open(cfg.MAME_STDERR_PATH.getPath(), 'wb') as err:
        p = subprocess.Popen([mame_prog_FN.getPath(), '-listxml'], stdout = out, stderr = err, cwd = mame_dir)
        count = 0
        while p.poll() is None:
            time.sleep(1)
            count += 1
            pDialog.updateProgress(count)
    pDialog.endProgress()
    time_extracting = time.time()

    # Count number of machines. Useful for later progress dialogs and statistics.
    log_info('mame_extract_MAME_XML() Counting number of machines ...')
    pDialog.startProgress('Counting number of MAME machines...')
    total_machines = mame_count_MAME_machines(cfg.MAME_XML_PATH)
    pDialog.endProgress()
    log_info('mame_extract_MAME_XML() Found {} machines.'.format(total_machines))

    # Get XML file stat info.
    # See https://docs.python.org/3/library/os.html#os.stat_result
    statinfo = os.stat(XML_path_FN.getPath())

    # Get MAME version from the XML.
    xml_f = io.open(XML_path_FN.getPath(), 'rt', encoding = 'utf-8')
    xml_iter = ET.iterparse(xml_f, events = ("start", "end"))
    event, root = next(xml_iter)
    xml_f.close()
    ver_mame_str = root.attrib['build']
    ver_mame_int = mame_get_numerical_version(ver_mame_str)

    # Create the MAME XML control file. Only change used fields.
    XML_control_dic = db_new_MAME_XML_control_dic()
    db_safe_edit(XML_control_dic, 't_XML_extraction', time_extracting)
    db_safe_edit(XML_control_dic, 't_XML_preprocessing', time.time())
    db_safe_edit(XML_control_dic, 'total_machines', total_machines)
    db_safe_edit(XML_control_dic, 'st_size', statinfo.st_size)
    db_safe_edit(XML_control_dic, 'st_mtime', statinfo.st_mtime)
    db_safe_edit(XML_control_dic, 'ver_mame_int', ver_mame_int)
    db_safe_edit(XML_control_dic, 'ver_mame_str', ver_mame_str)
    utils_write_JSON_file(cfg.MAME_XML_CONTROL_PATH.getPath(), XML_control_dic, verbose = True)

# 1) Counts number of MAME machines
# 2) Creates MAME XML control file.
def mame_preprocess_RETRO_MAME2003PLUS(cfg, st_dic):
    pDialog = KodiProgressDialog()

    # In MAME 2003 Plus MAME XML is already extracted.
    XML_path_FN = FileName(cfg.settings['xml_2003_path'])

    # Count number of machines. Useful for later progress dialogs and statistics.
    log_info('mame_process_RETRO_MAME2003PLUS() Counting number of machines ...')
    pDialog.startProgress('Counting number of MAME machines...')
    total_machines = mame_count_MAME_machines(XML_path_FN)
    pDialog.endProgress()
    log_info('mame_process_RETRO_MAME2003PLUS() Found {} machines.'.format(total_machines))

    # Get XML file stat info.
    # See https://docs.python.org/3/library/os.html#os.stat_result
    statinfo = os.stat(XML_path_FN.getPath())

    # Get MAME version from the XML (although we know is MAME 2003 Plus).
    # In MAME 2003 Plus the MAME version is not in the XML file.
    ver_mame_str = MAME2003PLUS_VERSION_RAW
    ver_mame_int = mame_get_numerical_version(ver_mame_str)

    # Create the MAME XML control file. Only change used fields.
    XML_control_dic = db_new_MAME_XML_control_dic()
    db_safe_edit(XML_control_dic, 't_XML_preprocessing', time.time())
    db_safe_edit(XML_control_dic, 'total_machines', total_machines)
    db_safe_edit(XML_control_dic, 'st_size', statinfo.st_size)
    db_safe_edit(XML_control_dic, 'st_mtime', statinfo.st_mtime)
    db_safe_edit(XML_control_dic, 'ver_mame_int', ver_mame_int)
    db_safe_edit(XML_control_dic, 'ver_mame_str', ver_mame_str)
    utils_write_JSON_file(cfg.MAME_2003_PLUS_XML_CONTROL_PATH.getPath(), XML_control_dic, verbose = True)

# After this function of code we have:
# 1) Valid and verified for existence MAME_XML_path.
# 2) A valid XML_control_dic and the XML control file is created and/or current.
#
# Returns tuple (MAME_XML_path [FileName object], XML_control_FN [FileName object])
def mame_init_MAME_XML(cfg, st_dic, force_rebuild = False):
    log_info('mame_init_MAME_XML() Beginning extract/process of MAME.xml...')
    if cfg.settings['op_mode'] == OP_MODE_VANILLA and force_rebuild:
        log_info('Forcing rebuilding of Vanilla MAME XML.')
        MAME_XML_path = cfg.MAME_XML_PATH
        XML_control_FN = cfg.MAME_XML_CONTROL_PATH
        # Extract, count number of machines and create XML control file.
        mame_extract_MAME_XML(cfg, st_dic)
        if st_dic['abort']: return
    elif cfg.settings['op_mode'] == OP_MODE_VANILLA and not force_rebuild:
        process_XML_flag = False
        MAME_exe_path = FileName(cfg.settings['mame_prog'])
        MAME_XML_path = cfg.MAME_XML_PATH
        XML_control_FN = cfg.MAME_XML_CONTROL_PATH
        # Check that MAME executable exists.
        if not cfg.settings['mame_prog']:
            log_info('Vanilla MAME executable path is not set. Aborting.')
            kodi_set_error_status(st_dic, 'Vanilla MAME executable path is not set.')
            return
        if not MAME_exe_path.exists():
            log_info('Vanilla MAME executable file not found. Aborting.')
            kodi_set_error_status(st_dic, 'Vanilla MAME executable file not found.')
            return
        log_info('Vanilla MAME executable found.')
        # Check that extracted MAME XML exists.
        # In Vanilla MAME the XML file is extracted from the executable.
        if MAME_XML_path.exists():
            log_info('Vanilla MAME XML file found.')
            # Check that the XML control file exists.
            if XML_control_FN.exists():
                # Open the XML control file and check if the current version of the MAME executable
                # is the same as in the XML control file.
                # If so reset everything, if not use the cached information in the XML control file.
                log_info('Vanilla MAME XML control file found.')
                XML_control_dic = utils_load_JSON_file(XML_control_FN.getPath())
                mame_exe_version_str = mame_get_MAME_exe_version(cfg, MAME_exe_path)
                log_debug('XML_control_dic["ver_mame_str"] "{}"'.format(XML_control_dic['ver_mame_str']))
                log_debug('mame_exe_version_str "{}"'.format(mame_exe_version_str))
                if mame_exe_version_str != XML_control_dic['ver_mame_str']:
                    log_info('Vanilla MAME version is different from the version in the XML control file. '
                        'Forcing new preprocessing.')
                    process_XML_flag = True
                else:
                    log_info('XML control file up to date.')
                    process_XML_flag = False
            else:
                log_info('XML control file NOT found. Forcing XML preprocessing.')
                process_XML_flag = True
        else:
            log_info('Vanilla MAME XML file NOT found. Forcing XML preprocessing.')
            process_XML_flag = True
        # Only process MAME XML if needed.
        if process_XML_flag:
            # Extract, count number of machines and create XML control file.
            mame_extract_MAME_XML(cfg, st_dic)
            if st_dic['abort']: return
        else:
            log_info('Reusing previosly preprocessed Vanilla MAME XML.')
    elif cfg.settings['op_mode'] == OP_MODE_RETRO_MAME2003PLUS and force_rebuild:
        log_info('Forcing rebuilding of MAME 2003 Plus XML.')
        MAME_XML_path = FileName(cfg.settings['xml_2003_path'])
        XML_control_FN = cfg.MAME_2003_PLUS_XML_CONTROL_PATH
        # Count number of machines and create XML control file.
        mame_preprocess_RETRO_MAME2003PLUS(cfg, st_dic)
        if st_dic['abort']: return
    elif cfg.settings['op_mode'] == OP_MODE_RETRO_MAME2003PLUS and not force_rebuild:
        process_XML_flag = False
        MAME_XML_path = FileName(cfg.settings['xml_2003_path'])
        XML_control_FN = cfg.MAME_2003_PLUS_XML_CONTROL_PATH
        # Check that MAME 2003 Plus XML exists.
        if not cfg.settings['xml_2003_path']:
            log_info('MAME 2003 Plus XML path is not set. Aborting.')
            kodi_set_error_status(st_dic, 'MAME 2003 Plus XML path is not set.')
            return
        if not MAME_XML_path.exists():
            log_info('MAME 2003 Plus XML file not found. Aborting.')
            kodi_set_error_status(st_dic, 'MAME 2003 Plus XML file not found.')
            return
        log_info('MAME 2003 Plus XML found.')
        # Check that the XML control file exists.
        if XML_control_FN.exists():
            # Open the XML control file and check if mtime of current file is older than
            # the one stored in the XML control file.
            # If so reset everything, if not use the cached information in the XML control file.
            log_info('MAME 2003 XML control file found.')
            XML_control_dic = utils_load_JSON_file(XML_control_FN.getPath())
            statinfo = os.stat(MAME_XML_path.getPath())
            log_debug('XML_control_dic["st_mtime"] "{}"'.format(XML_control_dic['st_mtime']))
            log_debug('statinfo.st_mtime "{}"'.format(statinfo.st_mtime))
            if statinfo.st_mtime > XML_control_dic['st_mtime']:
                log_info('XML file is more recent than last preprocessing. Forcing new preprocessing.')
                process_XML_flag = True
            else:
                log_info('XML control up to date.')
                process_XML_flag = False
        else:
            log_info('XML control file not found. Forcing XML preprocessing.')
            process_XML_flag = True
        # Only process MAME XML if needed.
        if process_XML_flag:
            # Count number of machines and create XML control file.
            mame_preprocess_RETRO_MAME2003PLUS(cfg, st_dic)
            if st_dic['abort']: return
        else:
            log_info('Reusing previosly preprocessed MAME 2003 XML.')
    else:
        log_error('mame_build_MAME_main_database() Unknown op_mode "{}"'.format(cfg.settings['op_mode']))
        kodi_set_error_status(st_dic, 'Unknown operation mode {}'.format(cfg.settings['op_mode']))
        return

    return MAME_XML_path, XML_control_FN

# -------------------------------------------------------------------------------------------------
# Loading of data files
# -------------------------------------------------------------------------------------------------
# Catver.ini is very special so it has a custom loader.
# It provides data for two catalogs: categories and version added. In other words, it
# has 2 folders defined in the INI file.
#
# --- Example -----------------------------------
# ;; Comment
# [special_folder_name or no mae]
# machine_name_1 = category_name_1
# machine_name_2 = category_name_2
# -----------------------------------------------
#
# Returns two dictionaries with struct similar a mame_load_INI_datfile_simple()
# catver_dic, veradded_dic
#
def mame_load_Catver_ini(filename):
    __debug_do_list_categories = False
    log_info('mame_load_Catver_ini() Parsing "{}"'.format(filename))
    catver_dic = {
        'version' : 'unknown',
        'unique_categories' : True,
        'single_category' : False,
        'isValid' : False,
        'data' : {},
        'categories' : set(),
    }
    veradded_dic = {
        'version' : 'unknown',
        'unique_categories' : True,
        'single_category' : False,
        'isValid' : False,
        'data' : {},
        'categories' : set(),
    }

    # --- read_status FSM values ---
    # 0 -> Looking for '[Category]' tag
    # 1 -> Reading categories
    # 2 -> Looking for '[VerAdded]' tag.
    # 3 -> Reading version added
    # 4 -> END
    read_status = 0
    try:
        f = io.open(filename, 'rt', encoding = 'utf-8')
    except IOError:
        log_error('mame_load_Catver_ini() Exception IOError')
        log_error('mame_load_Catver_ini() File "{}"'.format(filename))
        return (catver_dic, veradded_dic)
    for cat_line in f:
        stripped_line = cat_line.strip()
        if __debug_do_list_categories: log_debug('Line "' + stripped_line + '"')
        if read_status == 0:
            # >> Look for Catver version
            m = re.search(r'^;; CatVer ([0-9\.]+) / ', stripped_line)
            if m:
                catver_dic['version'] = m.group(1)
                veradded_dic['version'] = m.group(1)
            m = re.search(r'^;; CATVER.ini ([0-9\.]+) / ', stripped_line)
            if m:
                catver_dic['version'] = m.group(1)
                veradded_dic['version'] = m.group(1)
            if stripped_line == '[Category]':
                if __debug_do_list_categories: log_debug('Found [Category]')
                read_status = 1
        elif read_status == 1:
            line_list = stripped_line.split("=")
            if len(line_list) == 1:
                # log_debug('mame_load_Catver_ini() Reached end of categories parsing.')
                read_status = 2
            else:
                if __debug_do_list_categories: log_debug(line_list)
                machine_name = line_list[0]
                current_category = line_list[1]
                catver_dic['categories'].add(current_category)
                if machine_name in catver_dic['data']:
                    catver_dic['data'][machine_name].append(current_category)
                else:
                    catver_dic['data'][machine_name] = [current_category]
        elif read_status == 2:
            if stripped_line == '[VerAdded]':
                if __debug_do_list_categories: log_debug('Found [VerAdded]')
                read_status = 3
        elif read_status == 3:
            line_list = stripped_line.split("=")
            if len(line_list) == 1:
                # log_debug('mame_load_Catver_ini() Reached end of veradded parsing.')
                read_status = 4
            else:
                if __debug_do_list_categories: log_debug(line_list)
                machine_name = line_list[0]
                current_category = line_list[1]
                veradded_dic['categories'].add(current_category)
                if machine_name in veradded_dic['data']:
                    veradded_dic['data'][machine_name].append(current_category)
                else:
                    veradded_dic['data'][machine_name] = [current_category]
        elif read_status == 4:
            log_debug('End parsing')
            break
        else:
            raise CriticalError('Unknown read_status FSM value')
    f.close()
    catver_dic['single_category'] = True if len(catver_dic['categories']) == 1 else False
    for m_name in sorted(catver_dic['data']):
        if len(catver_dic['data'][m_name]) > 1:
            catver_dic['unique_categories'] = False
            break
    catver_dic['single_category'] = True
    veradded_dic['single_category'] = True if len(veradded_dic['categories']) == 1 else False
    for m_name in sorted(veradded_dic['data']):
        if len(veradded_dic['data'][m_name]) > 1:
            veradded_dic['unique_categories'] = False
            break
    veradded_dic['single_category'] = True
    # If categories are unique for each machine transform lists into strings
    if catver_dic['unique_categories']:
        for m_name in catver_dic['data']:
            catver_dic['data'][m_name] = catver_dic['data'][m_name][0]
    if veradded_dic['unique_categories']:
        for m_name in veradded_dic['data']:
            veradded_dic['data'][m_name] = veradded_dic['data'][m_name][0]
    log_info('mame_load_Catver_ini() Catver Machines   {:6d}'.format(len(catver_dic['data'])))
    log_info('mame_load_Catver_ini() Catver Categories {:6d}'.format(len(catver_dic['categories'])))
    log_info('mame_load_Catver_ini() Catver Version "{}"'.format(catver_dic['version']))
    log_info('mame_load_Catver_ini() Catver unique_categories {}'.format(catver_dic['unique_categories']))
    log_info('mame_load_Catver_ini() Catver single_category   {}'.format(catver_dic['single_category']))
    log_info('mame_load_Catver_ini() Veradded Machines   {:6d}'.format(len(veradded_dic['data'])))
    log_info('mame_load_Catver_ini() Veradded Categories {:6d}'.format(len(veradded_dic['categories'])))
    log_info('mame_load_Catver_ini() Veradded Version "{}"'.format(veradded_dic['version']))
    log_info('mame_load_Catver_ini() Veradded unique_categories {}'.format(veradded_dic['unique_categories']))
    log_info('mame_load_Catver_ini() Veradded single_category   {}'.format(veradded_dic['single_category']))

    return (catver_dic, veradded_dic)

#
# nplayers.ini does not have [ROOT_FOLDER], only [NPlayers].
# nplayers.ini has an structure very similar to catver.ini, and it is also supported here.
# Returns a ini_dic with same structue as mame_load_INI_datfile_simple()
#
# NOTE  nplayers.ini has defects like having repeated entries for some machines.
#       Do not crash because of this! For example (in verrsion 0.194 04-feb-18)
#       1943=2P sim
#       1943=2P sim
#
def mame_load_nplayers_ini(filename):
    __debug_do_list_categories = False
    log_info('mame_load_nplayers_ini() Parsing "{}"'.format(filename))
    ini_dic = {
        'version' : 'unknown',
        'unique_categories' : True,
        'single_category' : False,
        'isValid' : False,
        'data' : {},
        'categories' : set(),
    }

    # --- read_status FSM values ---
    # 0 -> Looking for '[NPlayers]' tag
    # 1 -> Reading categories
    # 2 -> Categories finished. STOP
    read_status = 0
    try:
        f = io.open(filename, 'rt', encoding = 'utf-8')
    except IOError:
        log_info('mame_load_nplayers_ini() (IOError) opening "{}"'.format(filename))
        return ini_dic
    for cat_line in f:
        stripped_line = cat_line.strip()
        if __debug_do_list_categories: log_debug('Line "' + stripped_line + '"')
        if read_status == 0:
            m = re.search(r'NPlayers ([0-9\.]+) / ', stripped_line)
            if m: ini_dic['version'] = m.group(1)
            if stripped_line == '[NPlayers]':
                if __debug_do_list_categories: log_debug('Found [NPlayers]')
                read_status = 1
        elif read_status == 1:
            line_list = stripped_line.split("=")
            if len(line_list) == 1:
                read_status = 2
                continue
            else:
                machine_name, current_category = text_type(line_list[0]), text_type(line_list[1])
                if __debug_do_list_categories: log_debug('"{}" / "{}"'.format(machine_name, current_category))
                ini_dic['categories'].add(current_category)
                if machine_name in ini_dic['data']:
                    # Force a single category to avoid nplayers.ini bugs.
                    pass
                    # ini_dic['data'][machine_name].add(current_category)
                    # log_debug('machine "{}"'.format(machine_name))
                    # log_debug('current_category "{}"'.format(current_category))
                    # log_debug('"{}"'.format(text_type(ini_dic['data'][machine_name])))
                    # raise ValueError('unique_categories False')
                else:
                    ini_dic['data'][machine_name] =  [current_category]
        elif read_status == 2:
            log_info('mame_load_nplayers_ini() Reached end of nplayers parsing.')
            break
        else:
            raise ValueError('Unknown read_status FSM value')
    f.close()
    ini_dic['single_category'] = True if len(ini_dic['categories']) == 1 else False
    # nplayers.ini has repeated machines, so checking for unique_cateogories is here.
    for m_name in sorted(ini_dic['data']):
        if len(ini_dic['data'][m_name]) > 1:
            ini_dic['unique_categories'] = False
            break
    # If categories are unique for each machine transform lists into strings
    if ini_dic['unique_categories']:
        for m_name in ini_dic['data']:
            ini_dic['data'][m_name] = ini_dic['data'][m_name][0]
    log_info('mame_load_nplayers_ini() Machines   {0:6d}'.format(len(ini_dic['data'])))
    log_info('mame_load_nplayers_ini() Categories {0:6d}'.format(len(ini_dic['categories'])))
    log_info('mame_load_nplayers_ini() Version "{}"'.format(ini_dic['version']))
    log_info('mame_load_nplayers_ini() unique_categories {}'.format(ini_dic['unique_categories']))
    log_info('mame_load_nplayers_ini() single_category   {}'.format(ini_dic['single_category']))

    # DEBUG: print machines with more than one category.
    # for m_name in sorted(ini_dic['data']):
    #     if len(ini_dic['data'][m_name]) > 1:
    #         for cat_name in ini_dic['data'][m_name]:
    #             log_debug('machine {} nplayers {}'.format(m_name, cat_name))

    return ini_dic

#
# Load mature.ini file.
# Returns a ini_dic similar to mame_load_INI_datfile_simple()
#
def mame_load_Mature_ini(filename):
    # FSM statuses
    FSM_HEADER = 0        # Looking for and process '[ROOT_FOLDER]' directory tag.
                          # Initial status.
    FSM_FOLDER_NAME = 1   # Searching for [category_name] and/or adding machines.

    log_info('mame_load_Mature_ini() Parsing "{}"'.format(filename))
    ini_dic = {
        'version' : 'unknown',
        'unique_categories' : True,
        'single_category' : False,
        'isValid' : False,
        'data' : {},
        'categories' : set(),
    }
    slist = []
    try:
        f = io.open(filename, 'rt', encoding = 'utf-8')
        for file_line in f:
            stripped_line = file_line.strip()
            if stripped_line == '': continue # Skip blanks
            slist.append(stripped_line)
        f.close()
    except IOError:
        log_info('mame_load_Mature_ini() (IOError) opening "{}"'.format(filename))
        return ini_dic

    fsm_status = FSM_HEADER
    for stripped_line in slist:
        if fsm_status == FSM_HEADER:
            # Skip comments: lines starting with ';;'
            # Look for version string in comments
            if re.search(r'^;;', stripped_line):
                # log_debug('mame_load_Mature_ini() Comment line "{}"'.format(stripped_line))
                m = re.search(r';; (\w+)\.ini ([0-9\.]+) / ', stripped_line)
                if m:
                    ini_dic['version'] = m.group(2)
                continue
            if stripped_line == '[ROOT_FOLDER]':
                fsm_status = FSM_FOLDER_NAME
                # Create default category
                current_category = 'default'
                ini_dic['categories'].add(current_category)
        elif fsm_status == FSM_FOLDER_NAME:
            machine_name = stripped_line
            if machine_name in ini_dic['data']:
                ini_dic['data'][machine_name].append(current_category)
            else:
                ini_dic['data'][machine_name] = [current_category]
        else:
            raise ValueError('Unknown FSM fsm_status {}'.format(fsm_status))
    ini_dic['single_category'] = True if len(ini_dic['categories']) == 1 else False
    for m_name in sorted(ini_dic['data']):
        if len(ini_dic['data'][m_name]) > 1:
            ini_dic['unique_categories'] = False
            break
    # If categories are unique for each machine transform lists into strings
    if ini_dic['unique_categories']:
        for m_name in ini_dic['data']:
            ini_dic['data'][m_name] = ini_dic['data'][m_name][0]
    log_info('mame_load_Mature_ini() Machines   {0:6d}'.format(len(ini_dic['data'])))
    log_info('mame_load_Mature_ini() Categories {0:6d}'.format(len(ini_dic['categories'])))
    log_info('mame_load_Mature_ini() Version "{}"'.format(ini_dic['version']))
    log_info('mame_load_Mature_ini() unique_categories {}'.format(ini_dic['unique_categories']))
    log_info('mame_load_Mature_ini() single_category   {}'.format(ini_dic['single_category']))

    return ini_dic

#
# Generic MAME INI file loader.
# Supports Alltime.ini, Artwork.ini, bestgames.ini, Category.ini, catlist.ini,
# genre.ini and series.ini.
#
# --- Example -----------------------------------
# ;; Comment
# [FOLDER_SETTINGS]
# RootFolderIcon mame
# SubFolderIcon folder
#
# [ROOT_FOLDER]
#
# [category_name_1]
# machine_name_1
# machine_name_2
#
# [category_name_2]
# machine_name_1
# -----------------------------------------------
#
# Note that some INIs, for example Artwork.ini, may have the same machine on different
# categories. This must be supported in this function.
#
# ini_dic = {
#     'version' : string,
#     'unique_categories' : bool,
#     'single_category' : bool,
#     'data' : {
#         'machine_name' : { 'category_1', 'category_2', ... }
#     }
#     'categories' : {
#         'category_1', 'category_2', ...
#     }
# }
#
# categories is a set of (unique) categories. By definition of set, each category appears
# only once.
# unique_categories is True is each machine has a unique category, False otherwise.
# single_category is True if only one category is defined, for example in mature.ini.
#
def mame_load_INI_datfile_simple(filename):
    # FSM statuses
    FSM_HEADER = 0        # Looking for and process '[ROOT_FOLDER]' directory tag.
                          # Initial status.
    FSM_FOLDER_NAME = 1   # Searching for [category_name] and/or adding machines.

    # Read file and put it in a list of strings.
    # Strings in this list are stripped.
    log_info('mame_load_INI_datfile_simple() Parsing "{}"'.format(filename))
    ini_dic = {
        'version' : 'unknown',
        'unique_categories' : True,
        'single_category' : False,
        'isValid' : False,
        'data' : {},
        'categories' : set(),
    }
    slist = []
    try:
        f = io.open(filename, 'rt', encoding = 'utf-8', errors = 'replace')
        for file_line in f:
            stripped_line = file_line.strip()
            if stripped_line == '': continue # Skip blanks
            slist.append(stripped_line)
        f.close()
    except IOError:
        log_info('mame_load_INI_datfile_simple() (IOError) opening "{}"'.format(filename))
        return ini_dic

    # Compile regexes to increase performance => It is no necessary. According to the docs: The
    # compiled versions of the most recent patterns passed to re.match(), re.search() or
    # re.compile() are cached, so programs that use only a few regular expressions at a
    # time needn’t worry about compiling regular expressions.
    fsm_status = FSM_HEADER
    for stripped_line in slist:
        # log_debug('{}'.format(stripped_line))
        if fsm_status == FSM_HEADER:
            # log_debug('FSM_HEADER "{}"'.format(stripped_line))
            # Skip comments: lines starting with ';;'
            # Look for version string in comments
            if re.search(r'^;;', stripped_line):
                m = re.search(r';; (\w+)\.ini ([0-9\.]+) / ', stripped_line)
                if m: ini_dic['version'] = m.group(2)
                continue
            if stripped_line.find('[ROOT_FOLDER]') >= 0:
                fsm_status = FSM_FOLDER_NAME
        elif fsm_status == FSM_FOLDER_NAME:
            m = re.search(r'^\[(.*)\]', stripped_line)
            if m:
                current_category = text_type(m.group(1))
                if current_category in ini_dic['categories']:
                    raise ValueError('Repeated category {}'.format(current_category))
                ini_dic['categories'].add(current_category)
            else:
                machine_name = stripped_line
                if machine_name in ini_dic['data']:
                    ini_dic['unique_categories'] = False
                    ini_dic['data'][machine_name].append(current_category)
                else:
                    ini_dic['data'][machine_name] = [current_category]
        else:
            raise ValueError('Unknown FSM fsm_status {}'.format(fsm_status))
    ini_dic['single_category'] = True if len(ini_dic['categories']) == 1 else False
    for m_name in sorted(ini_dic['data']):
        if len(ini_dic['data'][m_name]) > 1:
            ini_dic['unique_categories'] = False
            break
    # If categories are unique for each machine transform lists into strings
    if ini_dic['unique_categories']:
        for m_name in ini_dic['data']:
            ini_dic['data'][m_name] = ini_dic['data'][m_name][0]
    log_info('mame_load_INI_datfile_simple() Machines   {0:6d}'.format(len(ini_dic['data'])))
    log_info('mame_load_INI_datfile_simple() Categories {0:6d}'.format(len(ini_dic['categories'])))
    log_info('mame_load_INI_datfile_simple() Version "{}"'.format(ini_dic['version']))
    log_info('mame_load_INI_datfile_simple() unique_categories {}'.format(ini_dic['unique_categories']))
    log_info('mame_load_INI_datfile_simple() single_category   {}'.format(ini_dic['single_category']))

    return ini_dic

# --- BEGIN code in dev-parsers/test_parser_history_dat.py ----------------------------------------
# Loads History.dat. This function is deprecated in favour of the XML format.
#
# One description can be for several MAME machines:
#     $info=99lstwar,99lstwara,99lstwarb,
#     $bio
#
# One description can be for several SL items and several SL lists:
#     $amigaocs_flop=alloallo,alloallo1,
#     $amigaaga_flop=alloallo,alloallo1,
#     $amiga_flop=alloallo,alloallo1,
#     $bio
#
# key_in_history_dic is the first machine on the list on the first line.
#
# history_idx = {
#    'nes' : {
#        'name': string,
#        'machines' : {
#            'machine_name' : "beautiful_name|db_list_name|db_machine_name",
#            '100mandk' : "beautiful_name|nes|100mandk",
#            '89denku' : "beautiful_name|nes|89denku",
#        },
#    }
#    'mame' : {
#        'name' : string,
#        'machines': {
#            '88games' : "beautiful_name|db_list_name|db_machine_name",
#            'flagrall' : "beautiful_name|db_list_name|db_machine_name",
#        },
#    }
# }
#
# history_dic = {
#    'nes' : {
#        '100mandk' : string,
#        '89denku' : string,
#    },
#    'mame' : {
#        '88games' : string,
#        'flagrall' : string,
#    },
# }
def mame_load_History_DAT(filename):
    log_info('mame_load_History_DAT() Parsing "{}"'.format(filename))
    history_dic = {
        'version' : 'Unknown',
        'date' : 'Unknown',
        'index' : {},
        'data' : {},
    }
    __debug_function = False
    line_number = 0
    num_header_line = 0
    # Due to syntax errors in History.dat m_data may have invalid data, for example
    # exmpty strings as list_name and/or machine names.
    # m_data = [
    #     (line_number, list_name, [machine1, machine2, ...]),
    #     ...
    # ]
    m_data = []

    # Convenience variables.
    history_idx = history_dic['index']
    history_data = history_dic['data']

    # --- read_status FSM values ---
    # History.dat has some syntax errors, like empty machine names. To fix this, do
    # the parsing on two stages: first read the raw data and the bio and then
    # check if the data is OK before adding it to the index and the DB.
    # 0 -> Looking for '$info=machine_name_1,machine_name_2,' or '$SL_name=item_1,item_2,'
    #      If '$bio' found go to 1.
    # 1 -> Reading information. If '$end' found go to 2.
    # 2 -> Add information to database if no errors. Then go to 0.
    read_status = 0
    try:
        f = io.open(filename, 'rt', encoding = 'utf-8')
    except IOError:
        log_info('mame_load_History_DAT() (IOError) opening "{}"'.format(filename))
        return history_dic
    for file_line in f:
        line_number += 1
        line_uni = file_line.strip()
        if __debug_function: log_debug('Line "{}"'.format(line_uni))
        if read_status == 0:
            # Skip comments: lines starting with '##'
            # Look for version string in comments
            if re.search(r'^##', line_uni):
                m = re.search(r'## REVISION\: ([0-9\.]+)$', line_uni)
                if m: history_dic['version'] = m.group(1) + ' DAT'
                continue
            if line_uni == '': continue
            # Machine list line
            # Parses lines like "$info=99lstwar,99lstwara,99lstwarb,"
            # Parses lines like "$info=99lstwar,99lstwara,99lstwarb"
            # History.dat has syntactic errors like "$dc=,".
            # History.dat has syntactic errors like "$megadriv=".
            m = re.search(r'^\$(.+?)=(.*?),?$', line_uni)
            if m:
                num_header_line += 1
                list_name = m.group(1)
                machine_name_raw = m.group(2)
                # Remove trailing ',' to fix history.dat syntactic errors like
                # "$snes_bspack=bsfami,,"
                if len(machine_name_raw) > 1 and machine_name_raw[-1] == ',':
                    machine_name_raw = machine_name_raw[:-1]
                # Transform some special list names
                if list_name in {'info', 'info,megatech', 'info,stv'}: list_name = 'mame'
                mname_list = machine_name_raw.split(',')
                m_data.append([num_header_line, list_name, mname_list])
                continue
            if line_uni == '$bio':
                read_status = 1
                info_str_list = []
                continue
            # If we reach this point it's an error.
            raise TypeError('Wrong header "{}" (line {:,})'.format(line_uni, line_number))
        elif read_status == 1:
            if line_uni == '$end':
                # Generate biography text.
                bio_str = '\n'.join(info_str_list)
                bio_str = bio_str[1:] if bio_str[0] == '\n' else bio_str
                bio_str = bio_str[:-1] if bio_str[-1] == '\n' else bio_str
                bio_str = bio_str.replace('\n\t\t', '')

                # Clean m_data of bad data due to History.dat syntax errors, for example
                # empty machine names.
                # clean_m_data = [
                #     (list_name, [machine_name_1, machine_name_2, ...] ),
                #     ...,
                # ]
                clean_m_data = []
                for dtuple in m_data:
                    line_num, list_name, mname_list = dtuple
                    # If list_name is empty drop the full line
                    if not list_name: continue
                    # Clean empty machine names.
                    clean_mname_list = []
                    for machine_name in mname_list:
                        # Skip bad/wrong machine names.
                        if not machine_name: continue
                        if machine_name == ',': continue
                        clean_mname_list.append(machine_name)
                    clean_m_data.append((list_name, clean_mname_list))

                # Reset FSM status
                read_status = 2
                num_header_line = 0
                m_data = []
                info_str_list = []
            else:
                info_str_list.append(line_uni)
        elif read_status == 2:
            # Go to state 0 of the FSM.
            read_status = 0

            # Ignore machine if no valid data at all.
            if len(clean_m_data) == 0:
                log_warning('On History.dat line {:,}'.format(line_number))
                log_warning('clean_m_data is empty.')
                log_warning('Ignoring entry in History.dat database')
                continue
            # Ignore if empty list name.
            if not clean_m_data[0][0]:
                log_warning('On History.dat line {:,}'.format(line_number))
                log_warning('clean_m_data empty list name.')
                log_warning('Ignoring entry in History.dat database')
                continue
            # Ignore if empty machine list.
            if not clean_m_data[0][1]:
                log_warning('On History.dat line {:,}'.format(line_number))
                log_warning('Empty machine name list.')
                log_warning('db_list_name "{}"'.format(clean_m_data[0][0]))
                log_warning('Ignoring entry in History.dat database')
                continue
            if not clean_m_data[0][1][0]:
                log_warning('On History.dat line {:,}'.format(line_number))
                log_warning('Empty machine name first element.')
                log_warning('db_list_name "{}"'.format(clean_m_data[0][0]))
                log_warning('Ignoring entry in History.dat database')
                continue
            db_list_name = clean_m_data[0][0]
            db_machine_name = clean_m_data[0][1][0]

            # Add list and machine names to index database.
            for dtuple in clean_m_data:
                list_name, machine_name_list = dtuple
                if list_name not in history_idx:
                    history_idx[list_name] = {'name' : list_name, 'machines' : {}}
                for machine_name in machine_name_list:
                    m_str = misc_build_db_str_3(machine_name, db_list_name, db_machine_name)
                    history_idx[list_name]['machines'][machine_name] = m_str

            # Add biography string to main database.
            if db_list_name not in history_data: history_data[db_list_name] = {}
            history_data[db_list_name][db_machine_name] = bio_str
        else:
            raise TypeError('Wrong read_status = {} (line {:,})'.format(read_status, line_number))
    f.close()
    log_info('mame_load_History_DAT() Version "{}"'.format(history_dic['version']))
    log_info('mame_load_History_DAT() Rows in index {}'.format(len(history_dic['index'])))
    log_info('mame_load_History_DAT() Rows in data {}'.format(len(history_dic['data'])))
    return history_dic
# --- END code in dev-parsers/test_parser_history_dat.py ------------------------------------------

# --- BEGIN code in dev-parsers/test_parser_history_xml.py ----------------------------------------
# Loads History.xml, a new XML version of History.dat
#
# MAME machine:
# <entry>
#     <systems>
#     <system name="dino" />
#     <system name="dinou" />
#     </systems>
#     <text />
# </entry>
#
# One description can be for several SL items and several SL lists:
# <entry>
#     <software>
#         <item list="snes" name="smw2jb" />
#         <item list="snes" name="smw2ja" />
#         <item list="snes" name="smw2j" />
#     </software>
#     <text />
# </entry>
#
# Example of a problematic entry:
# <entry>
#     <systems>
#         <system name="10yardj" />
#     </systems>
#     <software>
#         <item list="vgmplay" name="10yard" />
#     </software>
#     <text />
# </entry>
#
# The key in the data dictionary is the first machine found on history.xml
#
# history_dic = {
#     'version' : '2.32', # string
#     'date' : '2021-05-28', # string
#     'index' : {
#         'nes' : {
#             'name': 'nes', # string, later changed with beautiful name
#             'machines' : {
#                 'machine_name' : "beautiful_name|db_list_name|db_machine_name",
#                 '100mandk' : "beautiful_name|nes|100mandk",
#                 '89denku' : "beautiful_name|nes|89denku",
#             },
#         },
#         'mame' : {
#             'name' : string,
#             'machines': {
#                 '88games' : "beautiful_name|db_list_name|db_machine_name",
#                 'flagrall' : "beautiful_name|db_list_name|db_machine_name",
#             },
#         },
#     },
#     'data' = {
#         'nes' : {
#             '100mandk' : string,
#             '89denku' : string,
#         },
#         'mame' : {
#             '88games' : string,
#             'flagrall' : string,
#         },
#     }
# }
def mame_load_History_xml(filename):
    log_info('mame_load_History_xml() Parsing "{}"'.format(filename))
    history_dic = {
        'version' : 'Unknown',
        'date' : 'Unknown',
        'index' : {},
        'data' : {},
    }
    __debug_xml_parser = False
    entry_counter = 0
    # Convenience variables.
    history_idx = history_dic['index']
    history_data = history_dic['data']

    xml_tree = utils_load_XML_to_ET(filename)
    if not xml_tree: return history_dic
    xml_root = xml_tree.getroot()
    history_dic['version'] = xml_root.attrib['version'] + ' XML ' + xml_root.attrib['date']
    history_dic['date'] = xml_root.attrib['date']
    for root_el in xml_root:
        if __debug_xml_parser: log_debug('Root child tag "{}"'.format(root_el.tag))
        if root_el.tag != 'entry':
            log_error('Unknown tag <{}>'.format(root_el.tag))
            raise TypeError
        entry_counter += 1
        item_list = []
        for entry_el in root_el:
            if __debug_xml_parser: log_debug('Entry child tag "{}"'.format(entry_el.tag))
            if entry_el.tag == 'software':
                for software_el in entry_el:
                    if software_el.tag != 'item':
                        log_error('Unknown <software> child tag <{}>'.format(software_el.tag))
                        raise TypeError
                    item_list.append((software_el.attrib['list'], software_el.attrib['name']))
            elif entry_el.tag == 'systems':
                for system_el in entry_el:
                    if system_el.tag != 'system':
                        log_error('Unknown <systems> child tag <{}>'.format(software_el.tag))
                        raise TypeError
                    item_list.append(('mame', software_el.attrib['name']))
            elif entry_el.tag == 'text':
                # Generate biography text.
                bio_str = entry_el.text
                bio_str = bio_str[1:] if bio_str[0] == '\n' else bio_str
                bio_str = bio_str[:-1] if bio_str[-1] == '\n' else bio_str
                bio_str = bio_str.replace('\n\t\t', '')

                # Add list and machine names to index database.
                if len(item_list) < 1:
                    log_warning('Empty item_list in entry_counter = {}'.format(entry_counter))
                    continue
                db_list_name = item_list[0][0]
                db_machine_name = item_list[0][1]
                for list_name, machine_name in item_list:
                    m_str = misc_build_db_str_3(machine_name, db_list_name, db_machine_name)
                    try:
                        history_idx[list_name]['machines'][machine_name] = m_str
                    except:
                        history_idx[list_name] = {'name' : list_name, 'machines' : {}}
                        history_idx[list_name]['machines'][machine_name] = m_str

                # Add biography string to main database.
                try:
                    history_data[db_list_name][db_machine_name] = bio_str
                except:
                    history_data[db_list_name] = {}
                    history_data[db_list_name][db_machine_name] = bio_str
            else:
                log_error('Unknown tag <{}>'.format(root_el.tag))
                raise TypeError
        if __debug_xml_parser and entry_counter > 100: break
    log_info('mame_load_History_xml() Version "{}"'.format(history_dic['version']))
    log_info('mame_load_History_xml() Date "{}"'.format(history_dic['date']))
    log_info('mame_load_History_xml() Rows in index {}'.format(len(history_dic['index'])))
    log_info('mame_load_History_xml() Rows in data {}'.format(len(history_dic['data'])))
    return history_dic
# --- END code in dev-parsers/test_parser_history_xml.py ------------------------------------------

# --- BEGIN code in dev-parsers/test_parser_mameinfo_dat.py ---------------------------------------
# mameinfo.dat has information for both MAME machines and MAME drivers.
#
# idx_dic  = {
#     'mame' : {
#         '88games' : 'beautiful_name',
#         'flagrall' : 'beautiful_name',
#     },
#     'drv' : {
#         '88games.cpp' : 'beautiful_name'],
#         'flagrall.cpp' : 'beautiful_name'],
#     }
# }
# data_dic = {
#    'mame' : {
#        '88games' : string,
#        'flagrall' : string,
#     },
#    'drv' : {
#        '1942.cpp' : string,
#        '1943.cpp' : string,
#    }
# }
def mame_load_MameInfo_DAT(filename):
    log_info('mame_load_MameInfo_DAT() Parsing "{}"'.format(filename))
    ret_dic = {
        'version' : 'Unknown',
        'index' : {
            'mame' : {},
            'drv' : {},
        },
        'data' : {},
    }
    __debug_function = False
    line_counter = 0

    # --- read_status FSM values ---
    # 0 -> Looking for '$(xxxx)=(machine_name)'
    # 1 -> Looking for $bio
    # 2 -> Reading information. If '$end' found go to 0.
    # 3 -> Ignoring information. If '$end' found go to 0.
    read_status = 0
    try:
        f = io.open(filename, 'rt', encoding = 'utf-8')
    except IOError:
        log_info('mame_load_MameInfo_DAT() (IOError) opening "{}"'.format(filename))
        return ret_dic
    for file_line in f:
        line_counter += 1
        line_uni = file_line.strip()
        # if __debug_function: log_debug('Line "{}"'.format(line_uni))
        if read_status == 0:
            # Skip comments: lines starting with '#'
            # Look for version string in comments
            if re.search(r'^#', line_uni):
                m = re.search(r'# MAMEINFO.DAT v([0-9\.]+)', line_uni)
                if m: ret_dic['version'] = m.group(1)
                continue
            if line_uni == '': continue
            # New machine or driver information
            m = re.search(r'^\$info=(.+?)$', line_uni)
            if m:
                machine_name = m.group(1)
                if __debug_function: log_debug('Machine "{}"'.format(machine_name))
                read_status = 1
        elif read_status == 1:
            if __debug_function: log_debug('Second line "{}"'.format(line_uni))
            if line_uni == '$mame':
                read_status = 2
                info_str_list = []
                list_name = 'mame'
                ret_dic['index'][list_name][machine_name] = machine_name
            elif line_uni == '$drv':
                read_status = 2
                info_str_list = []
                list_name = 'drv'
                ret_dic['index'][list_name][machine_name] = machine_name
            # Ignore empty lines between "$info=xxxxx" and "$mame" or "$drv"
            elif line_uni == '':
                continue
            else:
                raise TypeError('Wrong second line = "{}" (line {:,})'.format(line_uni, line_counter))
        elif read_status == 2:
            if line_uni == '$end':
                if list_name not in ret_dic['data']: ret_dic['data'][list_name] = {}
                ret_dic['data'][list_name][machine_name] = '\n'.join(info_str_list).strip()
                read_status = 0
            else:
                info_str_list.append(line_uni)
        else:
            raise TypeError('Wrong read_status = {} (line {:,})'.format(read_status, line_counter))
    f.close()
    log_info('mame_load_MameInfo_DAT() Version "{}"'.format(ret_dic['version']))
    log_info('mame_load_MameInfo_DAT() Rows in index {}'.format(len(ret_dic['index'])))
    log_info('mame_load_MameInfo_DAT() Rows in data {}'.format(len(ret_dic['data'])))
    return ret_dic
# --- END code in dev-parsers/test_parser_mameinfo_dat.py -----------------------------------------

# NOTE set objects are not JSON-serializable. Use lists and transform lists to sets if
#      necessary after loading the JSON file.
#
# idx_dic  = {
#     '88games', 'beautiful_name',
#     'flagrall', 'beautiful_name',
# }
# data_dic = {
#     '88games' : 'string',
#     'flagrall' : 'string',
# }
def mame_load_GameInit_DAT(filename):
    log_info('mame_load_GameInit_DAT() Parsing "{}"'.format(filename))
    ret_dic = {
        'version' : 'Unknown',
        'index' : {},
        'data' : {},
    }
    __debug_function = False

    # --- read_status FSM values ---
    # 0 -> Looking for '$info=(machine_name)'
    # 1 -> Looking for $mame
    # 2 -> Reading information. If '$end' found go to 0.
    # 3 -> Ignoring information. If '$end' found go to 0.
    read_status = 0
    try:
        f = io.open(filename, 'rt', encoding = 'utf-8')
    except IOError:
        log_info('mame_load_GameInit_DAT() (IOError) opening "{}"'.format(filename))
        return ret_dic
    for file_line in f:
        line_uni = file_line.strip()
        if __debug_function: log_debug('read_status {} | Line "{}"'.format(read_status, line_uni))
        # Note that Gameinit.dat may have a BOM 0xEF,0xBB,0xBF
        # See https://en.wikipedia.org/wiki/Byte_order_mark
        # Remove BOM if present.
        if line_uni and line_uni[0] == '\ufeff': line_uni = line_uni[1:]
        if read_status == 0:
            # Skip comments: lines starting with '#'
            # Look for version string in comments
            if re.search(r'^#', line_uni):
                if __debug_function: log_debug('Comment | "{}"'.format(line_uni))
                m = re.search(r'# MAME GAMEINIT\.DAT v([0-9\.]+) ', line_uni)
                if m: ret_dic['version'] = m.group(1)
                continue
            if line_uni == '': continue
            # New machine or driver information
            m = re.search(r'^\$info=(.+?)$', line_uni)
            if m:
                machine_name = m.group(1)
                if __debug_function: log_debug('Machine "{}"'.format(machine_name))
                ret_dic['index'][machine_name] = machine_name
                read_status = 1
        elif read_status == 1:
            if __debug_function: log_debug('Second line "{}"'.format(line_uni))
            if line_uni == '$mame':
                read_status = 2
                info_str_list = []
            else:
                raise TypeError('Wrong second line = "{}"'.format(line_uni))
        elif read_status == 2:
            if line_uni == '$end':
                ret_dic['data'][machine_name] = '\n'.join(info_str_list)
                info_str_list = []
                read_status = 0
            else:
                info_str_list.append(line_uni)
        else:
            raise TypeError('Wrong read_status = {}'.format(read_status))
    f.close()
    log_info('mame_load_GameInit_DAT() Version "{}"'.format(ret_dic['version']))
    log_info('mame_load_GameInit_DAT() Rows in index {}'.format(len(ret_dic['index'])))
    log_info('mame_load_GameInit_DAT() Rows in data {}'.format(len(ret_dic['data'])))
    return ret_dic

# NOTE set objects are not JSON-serializable. Use lists and transform lists to sets if
#      necessary after loading the JSON file.
#
# idx_dic  = {
#     '88games', 'beautiful_name',
#     'flagrall', 'beautiful_name',
# }
# data_dic = {
#     '88games' : 'string',
#     'flagrall' : 'string',
# }
def mame_load_Command_DAT(filename):
    log_info('mame_load_Command_DAT() Parsing "{}"'.format(filename))
    ret_dic = {
        'version' : 'Unknown',
        'index' : {},
        'data' : {},
    }
    # Temporal storage.
    idx_dic = {}
    data_dic = {}
    __debug_function = False

    # --- read_status FSM values ---
    # 0 -> Looking for '$info=(machine_name)'
    # 1 -> Looking for $cmd
    # 2 -> Reading information. If '$end' found go to 0.
    read_status = 0
    try:
        f = io.open(filename, 'rt', encoding = 'utf-8')
    except IOError:
        log_info('mame_load_Command_DAT() (IOError) opening "{}"'.format(filename))
        return ret_dic
    for file_line in f:
        line_uni = file_line.strip()
        # if __debug_function: log_debug('Line "{}"'.format(line_uni))
        if read_status == 0:
            # Skip comments: lines starting with '#'
            # Look for version string in comments
            if re.search(r'^#', line_uni):
                m = re.search(r'# Command List-[\w]+[\s]+([0-9\.]+) #', line_uni)
                if m: ret_dic['version'] = m.group(1)
                continue
            if line_uni == '': continue
            # New machine or driver information
            m = re.search(r'^\$info=(.+?)$', line_uni)
            if m:
                machine_name = m.group(1)
                if __debug_function: log_debug('Machine "{}"'.format(machine_name))
                idx_dic[machine_name] = machine_name
                read_status = 1
        elif read_status == 1:
            if __debug_function: log_debug('Second line "{}"'.format(line_uni))
            if line_uni == '$cmd':
                read_status = 2
                info_str_list = []
            else:
                raise TypeError('Wrong second line = "{}"'.format(line_uni))
        elif read_status == 2:
            if line_uni == '$end':
                data_dic[machine_name] = '\n'.join(info_str_list)
                info_str_list = []
                read_status = 0
            else:
                info_str_list.append(line_uni)
        else:
            raise TypeError('Wrong read_status = {}'.format(read_status))
    f.close()
    log_info('mame_load_Command_DAT() Version "{}"'.format(ret_dic['version']))
    log_info('mame_load_Command_DAT() Rows in idx_dic  {}'.format(len(idx_dic)))
    log_info('mame_load_Command_DAT() Rows in data_dic {}'.format(len(data_dic)))

    # Many machines share the same entry. Expand the database.
    for original_name in idx_dic:
        for expanded_name in original_name.split(','):
            # Skip empty strings
            if not expanded_name: continue
            expanded_name = expanded_name.strip()
            ret_dic['index'][expanded_name] = expanded_name
            ret_dic['data'][expanded_name] = data_dic[original_name]
    log_info('mame_load_Command_DAT() Entries in proper index  {}'.format(len(ret_dic['index'])))
    log_info('mame_load_Command_DAT() Entries in proper data {}'.format(len(ret_dic['data'])))
    return ret_dic

# -------------------------------------------------------------------------------------------------
# DAT export
# -------------------------------------------------------------------------------------------------
#
# Writes a XML text tag line, indented 2 spaces by default.
# Both tag_name and tag_text must be Unicode strings.
# Returns an Unicode string.
#
def XML_t(tag_name, tag_text = '', num_spaces = 4):
    if tag_text:
        tag_text = text_escape_XML(tag_text)
        line = '{}<{}>{}</{}>'.format(' ' * num_spaces, tag_name, tag_text, tag_name)
    else:
        # Empty tag
        line = '{}<{} />'.format(' ' * num_spaces, tag_name)

    return line

# Export a MAME information file in Billyc999 XML format to use with RCB.
# https://forum.kodi.tv/showthread.php?tid=70115&pid=2949624#pid2949624
# https://github.com/billyc999/Game-database-info
def mame_write_MAME_ROM_Billyc999_XML(cfg, out_dir_FN, db_dic):
    log_debug('mame_write_MAME_ROM_Billyc999_XML() BEGIN...')
    control_dic = db_dic['control_dic']

    # Get output filename
    # DAT filename: AML 0.xxx ROMs (merged|split|non-merged|fully non-merged).xml
    mame_version_str = control_dic['ver_mame_str']
    log_info('MAME version "{}"'.format(mame_version_str))
    DAT_basename_str = 'AML MAME {} Billyc999.xml'.format(mame_version_str)
    DAT_FN = out_dir_FN.pjoin(DAT_basename_str)
    log_info('XML "{}"'.format(DAT_FN.getPath()))

    # XML file header.
    sl = []
    sl.append('<?xml version="1.0" encoding="UTF-8"?>')
    sl.append('<menu>')
    sl.append('  <header>')
    sl.append(XML_t('listname', 'Exported by Advanced MAME Launcher'))
    sl.append(XML_t('lastlistupdate', misc_time_to_str(time.time())))
    sl.append(XML_t('listversion', '{}'.format(mame_version_str)))
    sl.append(XML_t('exporterversion', 'MAME {}'.format(mame_version_str)))
    sl.append('  </header>')

    # Traverse ROMs and write DAT.
    machine_counter = 0
    pDialog = KodiProgressDialog()
    pDialog.startProgress('Creating MAME Billyc999 XML...', len(db_dic['renderdb']))
    for m_name in sorted(db_dic['renderdb']):
        render = db_dic['renderdb'][m_name]
        assets = db_dic['assetdb'][m_name]
        sl.append('  <game name="{}">'.format(m_name))
        sl.append(XML_t('description', render['description']))
        sl.append(XML_t('year', render['year']))
        sl.append(XML_t('rating', 'ESRB - E (Everyone)'))
        sl.append(XML_t('manufacturer', render['manufacturer']))
        sl.append(XML_t('dev'))
        sl.append(XML_t('genre', render['genre']))
        sl.append(XML_t('score'))
        sl.append(XML_t('player', render['nplayers']))
        sl.append(XML_t('story', assets['plot']))
        sl.append(XML_t('enabled', 'Yes'))
        sl.append(XML_t('crc'))
        sl.append(XML_t('cloneof', render['cloneof']))
        sl.append('  </game>')
        machine_counter += 1
        pDialog.updateProgress(machine_counter)
    sl.append('</menu>')
    pDialog.endProgress()

    # Open output file name.
    pDialog.startProgress('Writing MAME Billyc999 XML...')
    utils_write_slist_to_file(DAT_FN.getPath(), sl)
    pDialog.endProgress()

#
# Only valid ROMs in DAT file.
#
def mame_write_MAME_ROM_XML_DAT(cfg, out_dir_FN, db_dic):
    log_debug('mame_write_MAME_ROM_XML_DAT() BEGIN...')
    control_dic = db_dic['control_dic']
    machines = db_dic['machines']
    render = db_dic['renderdb']
    audit_roms = db_dic['audit_roms']
    roms_sha1_dic = db_dic['roms_sha1_dic']

    # Get output filename
    # DAT filename: AML 0.xxx ROMs (merged|split|non-merged|fully non-merged).xml
    mame_version_str = control_dic['ver_mame_str']
    rom_set = ['MERGED', 'SPLIT', 'NONMERGED', 'FULLYNONMERGED'][cfg.settings['mame_rom_set']]
    rom_set_str = ['Merged', 'Split', 'Non-merged', 'Fully Non-merged'][cfg.settings['mame_rom_set']]
    log_info('MAME version "{}"'.format(mame_version_str))
    log_info('ROM set is "{}"'.format(rom_set_str))
    DAT_basename_str = 'AML MAME {} ROMs ({}).xml'.format(mame_version_str, rom_set_str)
    DAT_FN = out_dir_FN.pjoin(DAT_basename_str)
    log_info('XML "{}"'.format(DAT_FN.getPath()))

    # XML file header.
    slist = []
    slist.append('<?xml version="1.0" encoding="UTF-8"?>')
    slist.append('<!DOCTYPE datafile PUBLIC "{}" "{}">'.format(
        '-//Logiqx//DTD ROM Management Datafile//EN', 'http://www.logiqx.com/Dats/datafile.dtd'))
    slist.append('<datafile>')

    desc_str = 'AML MAME {} ROMs {} set'.format(mame_version_str, rom_set_str)
    slist.append('<header>')
    slist.append(XML_t('name', desc_str))
    slist.append(XML_t('description', desc_str))
    slist.append(XML_t('version', '{}'.format(mame_version_str)))
    slist.append(XML_t('date', misc_time_to_str(time.time())))
    slist.append(XML_t('author', 'Exported by Advanced MAME Launcher'))
    slist.append('</header>')

    # Traverse ROMs and write DAT.
    pDialog = KodiProgressDialog()
    pDialog.startProgress('Creating MAME ROMs XML DAT...', len(audit_roms))
    for m_name in sorted(audit_roms):
        pDialog.updateProgressInc()
        # If machine has no ROMs then skip it
        rom_list, actual_rom_list, num_ROMs = audit_roms[m_name], [], 0
        for rom in rom_list:
            # Skip CHDs and samples
            if rom['type'] == ROM_TYPE_ERROR: raise ValueError
            if rom['type'] in [ROM_TYPE_DISK, ROM_TYPE_SAMPLE]: continue
            # Skip machine ROMs not in this machine ZIP file.
            zip_name, rom_name = rom['location'].split('/')
            if zip_name != m_name: continue
            # Skip invalid ROMs
            if not rom['crc']: continue
            # Add SHA1 field
            rom['sha1'] = roms_sha1_dic[rom['location']]
            actual_rom_list.append(rom)
            num_ROMs += 1
        # Machine has no ROMs, skip it
        if num_ROMs == 0: continue

        # Print ROMs in the XML.
        slist.append('<machine name="{}">'.format(m_name))
        slist.append(XML_t('description', render[m_name]['description']))
        slist.append(XML_t('year', render[m_name]['year']))
        slist.append(XML_t('manufacturer', render[m_name]['manufacturer']))
        if render[m_name]['cloneof']:
            slist.append(XML_t('cloneof', render[m_name]['cloneof']))
        for rom in actual_rom_list:
            t = '    <rom name="{}" size="{}" crc="{}" sha1="{}"/>'.format(
                rom['name'], rom['size'], rom['crc'], rom['sha1'])
            slist.append(t)
        slist.append('</machine>')
    slist.append('</datafile>')
    pDialog.endProgress()

    # Open output file name.
    pDialog.startProgress('Writing MAME ROMs XML DAT...')
    utils_write_slist_to_file(DAT_FN.getPath(), slist)
    pDialog.endProgress()

#
# Only valid CHDs in DAT file.
#
def mame_write_MAME_CHD_XML_DAT(cfg, out_dir_FN, db_dic):
    log_debug('mame_write_MAME_CHD_XML_DAT() BEGIN ...')
    control_dic = db_dic['control_dic']
    machines = db_dic['machines']
    render = db_dic['renderdb']
    audit_roms = db_dic['audit_roms']

    # Get output filename
    # DAT filename: AML 0.xxx ROMs (merged|split|non-merged|fully non-merged).xml
    mame_version_str = control_dic['ver_mame_str']
    chd_set = ['MERGED', 'SPLIT', 'NONMERGED'][cfg.settings['mame_chd_set']]
    chd_set_str = ['Merged', 'Split', 'Non-merged'][cfg.settings['mame_chd_set']]
    log_info('MAME version "{}"'.format(mame_version_str))
    log_info('CHD set is "{}"'.format(chd_set_str))
    DAT_basename_str = 'AML MAME {} CHDs ({}).xml'.format(mame_version_str, chd_set_str)
    DAT_FN = out_dir_FN.pjoin(DAT_basename_str)
    log_info('XML "{}"'.format(DAT_FN.getPath()))

    # XML file header.
    slist = []
    slist.append('<?xml version="1.0" encoding="UTF-8"?>')
    str_a = '-//Logiqx//DTD ROM Management Datafile//EN'
    str_b = 'http://www.logiqx.com/Dats/datafile.dtd'
    slist.append('<!DOCTYPE datafile PUBLIC "{}" "{}">'.format(str_a, str_b))
    slist.append('<datafile>')

    desc_str = 'AML MAME {} CHDs {} set'.format(mame_version_str, chd_set_str)
    slist.append('<header>')
    slist.append(XML_t('name', desc_str))
    slist.append(XML_t('description', desc_str))
    slist.append(XML_t('version', '{}'.format(mame_version_str)))
    slist.append(XML_t('date', misc_time_to_str(time.time())))
    slist.append(XML_t('author', 'Exported by Advanced MAME Launcher'))
    slist.append('</header>')

    # Traverse ROMs and write DAT.
    pDialog = KodiProgressDialog()
    pDialog.startProgress('Creating MAME CHDs XML DAT...', len(audit_roms))
    for m_name in sorted(audit_roms):
        pDialog.updateProgressInc()
        # If machine has no ROMs then skip it
        chd_list, actual_chd_list, num_CHDs = audit_roms[m_name], [], 0
        for chd in chd_list:
            # Only include CHDs
            if chd['type'] != ROM_TYPE_DISK: continue
            # Skip machine ROMs not in this machine ZIP file.
            zip_name, chd_name = chd['location'].split('/')
            if zip_name != m_name: continue
            # Skip invalid CHDs
            if not chd['sha1']: continue
            actual_chd_list.append(chd)
            num_CHDs += 1
        if num_CHDs == 0: continue

        # Print CHDs in the XML.
        slist.append('<machine name="{}">'.format(m_name))
        slist.append(XML_t('description', render[m_name]['description']))
        slist.append(XML_t('year', render[m_name]['year']))
        slist.append(XML_t('manufacturer', render[m_name]['manufacturer']))
        if render[m_name]['cloneof']:
            slist.append(XML_t('cloneof', render[m_name]['cloneof']))
        for chd in actual_chd_list:
            t = '    <rom name="{}" sha1="{}"/>'.format(chd['name'], chd['sha1'])
            slist.append(t)
        slist.append('</machine>')
    slist.append('</datafile>')
    pDialog.endProgress()

    # Open output file name.
    pDialog.startProgress('Creating MAME ROMs XML DAT...')
    utils_write_slist_to_file(DAT_FN.getPath(), slist)
    pDialog.endProgress()

#
# -------------------------------------------------------------------------------------------------
# CHD manipulation functions
# -------------------------------------------------------------------------------------------------
# Reference in https://github.com/rtissera/libchdr/blob/master/src/chd.h
# Reference in https://github.com/mamedev/mame/blob/master/src/lib/util/chd.h
#
# Open CHD and return stat information.
#
# chd_info = {
#     'status'  : CHD_OK or CHD_BAD,
#     'version' : int,
#     'sha1'    : string,
# }
#
CHD_OK          = 0
CHD_BAD_CHD     = 1
CHD_BAD_VERSION = 2
def _mame_stat_chd(chd_path):
    __debug_this_function = False
    chd_info = {
        'status'  : CHD_OK,
        'version' : 0,
        'sha1'    : '',
    }

    # --- Open CHD file and read first 124 bytes ---
    if __debug_this_function: log_debug('_mame_stat_chd() Opening "{}"'.format(chd_path))
    try:
        f = io.open(chd_path, 'rb')
        chd_data_str = f.read(124)
        f.close()
    except IOError as E:
        chd_info['status'] = CHD_BAD_CHD
        return chd_info

    # --- Check CHD magic string to skip fake files ---
    if chd_data_str[0:8] != 'MComprHD':
        if __debug_this_function: log_debug('_mame_stat_chd() Magic string not found!')
        chd_info['status'] = CHD_BAD_CHD
        return chd_info

    # --- Parse CHD header ---
    # All values in the CHD header are stored in big endian!
    h_tuple = struct.unpack('>8sII', chd_data_str[0:16])
    tag, length, version = h_tuple
    if __debug_this_function:
        log_debug('_mame_stat_chd() Tag     "{}"'.format(tag))
        log_debug('_mame_stat_chd() Length  {}'.format(length))
        log_debug('_mame_stat_chd() Version {}'.format(version))

    # Discard very old CHD that don't have SHA1 hash. Older version used MD5.
    if version == 1 or version == 2 or version == 3:
        chd_info['status'] = CHD_BAD_VERSION
        chd_info['version'] = version
        return chd_info

    # Read the whole header (must consider V3, V4 and V5)
    # NOTE In MAME 0.196 some CHDs have version 4, most have version 5, version 3 is obsolete
    if version == 4:
        if __debug_this_function: log_debug('Reading V4 CHD header')
        chd_header_v4_str = '>8sIIIIIQQI20s20s20s'
        header_size = struct.calcsize(chd_header_v4_str)
        t = struct.unpack(chd_header_v4_str, chd_data_str[0:108])
        tag          = t[0]
        length       = t[1]
        version      = t[2]
        flags        = t[3]
        compression  = t[4]
        totalhunks   = t[5]
        logicalbytes = t[6]
        metaoffset   = t[7]
        hunkbytes    = t[8]
        rawsha1      = binascii.b2a_hex(t[9])
        sha1         = binascii.b2a_hex(t[10])
        parentsha1   = binascii.b2a_hex(t[11])

        if __debug_this_function:
            log_debug('V4 header size = {}'.format(header_size))
            log_debug('tag           "{}"'.format(tag))
            log_debug('length        {}'.format(length))
            log_debug('version       {}'.format(version))
            log_debug('flags         {}'.format(flags))
            log_debug('compression   {}'.format(compression))
            log_debug('totalhunks    {}'.format(totalhunks))
            log_debug('logicalbytes  {}'.format(logicalbytes))
            log_debug('metaoffset    {}'.format(metaoffset))
            log_debug('hunkbytes     {}'.format(hunkbytes))
            log_debug('rawsha1       "{}"'.format(rawsha1))
            log_debug('sha1          "{}"'.format(sha1))
            log_debug('parentsha1    "{}"'.format(parentsha1))

        # The CHD SHA1 string storet in MAME -listxml is the rawsha1 field in V4 CHDs.
        chd_info['status']  = CHD_OK
        chd_info['version'] = version
        chd_info['sha1']    = rawsha1
    elif version == 5:
        if __debug_this_function: log_debug('Reading V5 CHD header')
        chd_header_v5_str = '>8sII16sQQQII20s20s20s'
        header_size = struct.calcsize(chd_header_v5_str)
        t = struct.unpack(chd_header_v5_str, chd_data_str)
        tag           = t[0]
        length        = t[1]
        version       = t[2]
        compressors   = t[3]
        logicalbytes  = t[4]
        mapoffset     = t[5]
        metaoffset    = t[6]
        hunkbytes     = t[7]
        unitbytes     = t[8]
        rawsha1       = binascii.b2a_hex(t[9])
        sha1          = binascii.b2a_hex(t[10])
        parentsha1    = binascii.b2a_hex(t[11])

        if __debug_this_function:
            log_debug('V5 header size = {}'.format(header_size))
            log_debug('tag           "{}"'.format(tag))
            log_debug('length        {}'.format(length))
            log_debug('version       {}'.format(version))
            log_debug('compressors   "{}"'.format(compressors))
            log_debug('logicalbytes  {}'.format(logicalbytes))
            log_debug('mapoffset     {}'.format(mapoffset))
            log_debug('metaoffset    {}'.format(metaoffset))
            log_debug('hunkbytes     {}'.format(hunkbytes))
            log_debug('unitbytes     {}'.format(unitbytes))
            log_debug('rawsha1       "{}"'.format(rawsha1))
            log_debug('sha1          "{}"'.format(sha1))
            log_debug('parentsha1    "{}"'.format(parentsha1))

        # The CHD SHA1 string storet in MAME -listxml is the sha1 field (combined raw+meta SHA1).
        chd_info['status']  = CHD_OK
        chd_info['version'] = version
        chd_info['sha1']    = sha1
    else:
        raise TypeError('Unsuported version = {}'.format(version))

    return chd_info

# -------------------------------------------------------------------------------------------------
# Statistic printing
# -------------------------------------------------------------------------------------------------
def mame_info_MAME_print(slist, location, machine_name, machine, assets):
    slist.append('[COLOR orange]Machine {} / Render data[/COLOR]'.format(machine_name))
    # Print MAME Favourites special fields
    if 'ver_mame' in machine:
        slist.append("[COLOR slateblue]name[/COLOR]: {}".format(machine['name']))
    if 'ver_mame' in machine:
        slist.append("[COLOR slateblue]ver_mame[/COLOR]: {}".format(machine['ver_mame']))
    if 'ver_mame_str' in machine:
        slist.append("[COLOR slateblue]ver_mame_str[/COLOR]: {}".format(machine['ver_mame_str']))
    # Most Played Favourites special fields
    if 'launch_count' in machine:
        slist.append("[COLOR slateblue]launch_count[/COLOR]: {}".format(text_type(machine['launch_count'])))

    # Standard fields in Render database
    slist.append("[COLOR violet]cloneof[/COLOR]: '{}'".format(machine['cloneof']))
    slist.append("[COLOR violet]description[/COLOR]: '{}'".format(machine['description']))
    slist.append("[COLOR violet]driver_status[/COLOR]: '{}'".format(machine['driver_status']))
    slist.append("[COLOR violet]genre[/COLOR]: '{}'".format(machine['genre']))
    slist.append("[COLOR skyblue]isBIOS[/COLOR]: {}".format(machine['isBIOS']))
    slist.append("[COLOR skyblue]isDevice[/COLOR]: {}".format(machine['isDevice']))
    slist.append("[COLOR skyblue]isMature[/COLOR]: {}".format(machine['isMature']))
    slist.append("[COLOR violet]manufacturer[/COLOR]: '{}'".format(machine['manufacturer']))
    slist.append("[COLOR violet]nplayers[/COLOR]: '{}'".format(machine['nplayers']))
    slist.append("[COLOR violet]year[/COLOR]: '{}'".format(machine['year']))

    # Standard fields in Main database
    slist.append('\n[COLOR orange]Machine Main data[/COLOR]')
    slist.append("[COLOR skyblue]alltime[/COLOR]: {}".format(text_type(machine['alltime'])))
    slist.append("[COLOR skyblue]artwork[/COLOR]: {}".format(text_type(machine['artwork'])))
    slist.append("[COLOR violet]bestgames[/COLOR]: '{}'".format(machine['bestgames']))
    slist.append("[COLOR skyblue]category[/COLOR]: {}".format(text_type(machine['category'])))
    slist.append("[COLOR violet]catlist[/COLOR]: '{}'".format(machine['catlist']))
    slist.append("[COLOR violet]catver[/COLOR]: '{}'".format(machine['catver']))
    slist.append("[COLOR skyblue]chip_cpu_name[/COLOR]: {}".format(text_type(machine['chip_cpu_name'])))
    # --- Devices list is a special case ---
    if machine['devices']:
        for i, device in enumerate(machine['devices']):
            slist.append("[COLOR lime]devices[/COLOR][{}]:".format(i))
            slist.append("  [COLOR violet]att_type[/COLOR]: {}".format(device['att_type']))
            slist.append("  [COLOR violet]att_tag[/COLOR]: {}".format(device['att_tag']))
            slist.append("  [COLOR skyblue]att_mandatory[/COLOR]: {}".format(text_type(device['att_mandatory'])))
            slist.append("  [COLOR violet]att_interface[/COLOR]: {}".format(device['att_interface']))
            slist.append("  [COLOR skyblue]instance[/COLOR]: {}".format(text_type(device['instance'])))
            slist.append("  [COLOR skyblue]ext_names[/COLOR]: {}".format(text_type(device['ext_names'])))
    else:
        slist.append("[COLOR lime]devices[/COLOR]: []")
    slist.append("[COLOR skyblue]display_height[/COLOR]: {}".format(text_type(machine['display_height'])))
    slist.append("[COLOR skyblue]display_refresh[/COLOR]: {}".format(text_type(machine['display_refresh'])))
    slist.append("[COLOR skyblue]display_rotate[/COLOR]: {}".format(text_type(machine['display_rotate'])))
    slist.append("[COLOR skyblue]display_type[/COLOR]: {}".format(text_type(machine['display_type'])))
    slist.append("[COLOR skyblue]display_width[/COLOR]: {}".format(text_type(machine['display_width'])))
    slist.append("[COLOR violet]genre[/COLOR]: '{}'".format(machine['genre']))
    # --- input is a special case ---
    if machine['input']:
        # Print attributes
        slist.append("[COLOR lime]input[/COLOR]:")
        slist.append("  [COLOR skyblue]att_coins[/COLOR]: {}".format(text_type(machine['input']['att_coins'])))
        slist.append("  [COLOR skyblue]att_players[/COLOR]: {}".format(text_type(machine['input']['att_players'])))
        slist.append("  [COLOR skyblue]att_service[/COLOR]: {}".format(text_type(machine['input']['att_service'])))
        slist.append("  [COLOR skyblue]att_tilt[/COLOR]: {}".format(text_type(machine['input']['att_tilt'])))
        # Print control tag list
        for i, control in enumerate(machine['input']['control_list']):
            slist.append("[COLOR lime]control[/COLOR][{}]:".format(i))
            slist.append("  [COLOR violet]type[/COLOR]: {}".format(control['type']))
            slist.append("  [COLOR skyblue]player[/COLOR]: {}".format(text_type(control['player'])))
            slist.append("  [COLOR skyblue]buttons[/COLOR]: {}".format(text_type(control['buttons'])))
            slist.append("  [COLOR skyblue]ways[/COLOR]: {}".format(text_type(control['ways'])))
    else:
        slist.append("[COLOR lime]input[/COLOR]: []")
    slist.append("[COLOR skyblue]isDead[/COLOR]: {}".format(text_type(machine['isDead'])))
    slist.append("[COLOR skyblue]isMechanical[/COLOR]: {}".format(text_type(machine['isMechanical'])))
    slist.append("[COLOR violet]romof[/COLOR]: '{}'".format(machine['romof']))
    slist.append("[COLOR violet]sampleof[/COLOR]: '{}'".format(machine['sampleof']))
    slist.append("[COLOR skyblue]series[/COLOR]: '{}'".format(machine['series']))
    slist.append("[COLOR skyblue]softwarelists[/COLOR]: {}".format(text_type(machine['softwarelists'])))
    slist.append("[COLOR violet]sourcefile[/COLOR]: '{}'".format(machine['sourcefile']))
    slist.append("[COLOR violet]veradded[/COLOR]: '{}'".format(machine['veradded']))

    slist.append('\n[COLOR orange]Machine assets/artwork[/COLOR]')
    slist.append("[COLOR violet]3dbox[/COLOR]: '{}'".format(assets['3dbox']))
    slist.append("[COLOR violet]artpreview[/COLOR]: '{}'".format(assets['artpreview']))
    slist.append("[COLOR violet]artwork[/COLOR]: '{}'".format(assets['artwork']))
    slist.append("[COLOR violet]cabinet[/COLOR]: '{}'".format(assets['cabinet']))
    slist.append("[COLOR violet]clearlogo[/COLOR]: '{}'".format(assets['clearlogo']))
    slist.append("[COLOR violet]cpanel[/COLOR]: '{}'".format(assets['cpanel']))
    slist.append("[COLOR violet]fanart[/COLOR]: '{}'".format(assets['fanart']))
    slist.append("[COLOR violet]flags[/COLOR]: '{}'".format(assets['flags']))
    slist.append("[COLOR violet]flyer[/COLOR]: '{}'".format(assets['flyer']))
    slist.append("[COLOR violet]history[/COLOR]: '{}'".format(assets['history']))
    slist.append("[COLOR violet]manual[/COLOR]: '{}'".format(assets['manual']))
    slist.append("[COLOR violet]marquee[/COLOR]: '{}'".format(assets['marquee']))
    slist.append("[COLOR violet]PCB[/COLOR]: '{}'".format(assets['PCB']))
    slist.append("[COLOR violet]plot[/COLOR]: '{}'".format(assets['plot']))
    slist.append("[COLOR violet]snap[/COLOR]: '{}'".format(assets['snap']))
    slist.append("[COLOR violet]title[/COLOR]: '{}'".format(assets['title']))
    slist.append("[COLOR violet]trailer[/COLOR]: '{}'".format(assets['trailer']))

def mame_info_SL_print(slist, location, SL_name, SL_ROM, rom, assets, SL_dic, SL_machine_list):
    # --- ROM stuff ---
    slist.append('[COLOR orange]Software List {} Item {}[/COLOR]'.format(SL_name, SL_ROM))
    if 'SL_DB_key' in rom:
        slist.append("[COLOR slateblue]SL_DB_key[/COLOR]: '{}'".format(rom['SL_DB_key']))
    if 'SL_ROM_name' in rom:
        slist.append("[COLOR slateblue]SL_ROM_name[/COLOR]: '{}'".format(rom['SL_ROM_name']))
    if 'SL_name' in rom:
        slist.append("[COLOR slateblue]SL_name[/COLOR]: '{}'".format(rom['SL_name']))
    slist.append("[COLOR violet]cloneof[/COLOR]: '{}'".format(rom['cloneof']))
    slist.append("[COLOR violet]description[/COLOR]: '{}'".format(rom['description']))
    slist.append("[COLOR skyblue]hasCHDs[/COLOR]: {}".format(text_type(rom['hasCHDs'])))
    slist.append("[COLOR skyblue]hasROMs[/COLOR]: {}".format(text_type(rom['hasROMs'])))
    if 'launch_count' in rom:
        slist.append("[COLOR slateblue]launch_count[/COLOR]: '{}'".format(text_type(rom['launch_count'])))
    if 'launch_machine' in rom:
        slist.append("[COLOR slateblue]launch_machine[/COLOR]: '{}'".format(rom['launch_machine']))
    if rom['parts']:
        for i, part in enumerate(rom['parts']):
            slist.append("[COLOR lime]parts[/COLOR][{}]:".format(i))
            slist.append("  [COLOR violet]interface[/COLOR]: '{}'".format(part['interface']))
            slist.append("  [COLOR violet]name[/COLOR]: '{}'".format(part['name']))
    else:
        slist.append('[COLOR lime]parts[/COLOR]: []')
    slist.append("[COLOR violet]plot[/COLOR]: '{}'".format(rom['plot']))
    slist.append("[COLOR violet]publisher[/COLOR]: '{}'".format(rom['publisher']))
    slist.append("[COLOR violet]status_CHD[/COLOR]: '{}'".format(rom['status_CHD']))
    slist.append("[COLOR violet]status_ROM[/COLOR]: '{}'".format(rom['status_ROM']))
    if 'ver_mame' in rom:
        slist.append("[COLOR slateblue]ver_mame[/COLOR]: {}".format(rom['ver_mame']))
    if 'ver_mame_str' in rom:
        slist.append("[COLOR slateblue]ver_mame_str[/COLOR]: {}".format(rom['ver_mame_str']))
    slist.append("[COLOR violet]year[/COLOR]: '{}'".format(rom['year']))

    slist.append('\n[COLOR orange]Software List assets[/COLOR]')
    slist.append("[COLOR violet]3dbox[/COLOR]: '{}'".format(assets['3dbox']))
    slist.append("[COLOR violet]title[/COLOR]: '{}'".format(assets['title']))
    slist.append("[COLOR violet]snap[/COLOR]: '{}'".format(assets['snap']))
    slist.append("[COLOR violet]boxfront[/COLOR]: '{}'".format(assets['boxfront']))
    slist.append("[COLOR violet]fanart[/COLOR]: '{}'".format(assets['fanart']))
    slist.append("[COLOR violet]trailer[/COLOR]: '{}'".format(assets['trailer']))
    slist.append("[COLOR violet]manual[/COLOR]: '{}'".format(assets['manual']))

    slist.append('\n[COLOR orange]Software List {}[/COLOR]'.format(SL_name))
    slist.append("[COLOR violet]display_name[/COLOR]: '{}'".format(SL_dic['display_name']))
    slist.append("[COLOR skyblue]num_with_CHDs[/COLOR]: {}".format(text_type(SL_dic['num_with_CHDs'])))
    slist.append("[COLOR skyblue]num_with_ROMs[/COLOR]: {}".format(text_type(SL_dic['num_with_ROMs'])))
    slist.append("[COLOR violet]rom_DB_noext[/COLOR]: '{}'".format(SL_dic['rom_DB_noext']))

    slist.append('\n[COLOR orange]Runnable by[/COLOR]')
    for machine_dic in sorted(SL_machine_list, key = lambda x: x['description'].lower()):
        t = "[COLOR violet]machine[/COLOR]: '{}' [COLOR slateblue]{}[/COLOR]"
        slist.append(t.format(machine_dic['description'], machine_dic['machine']))

# slist is a list of strings that will be joined like '\n'.join(slist)
# slist is a list, so it is mutable and can be changed by reference.
def mame_stats_main_print_slist(cfg, slist, control_dic, XML_ctrl_dic):
    settings = cfg.settings
    ctrl = control_dic
    SL_str = 'enabled' if settings['global_enable_SL'] else 'disabled'

    slist.append('[COLOR orange]Main information[/COLOR]')
    slist.append('AML version            {:,} [COLOR violet]{}[/COLOR]'.format(
        cfg.addon_version_int, cfg.addon.info_version))
    slist.append('Database version       {:,} [COLOR violet]{}[/COLOR]'.format(
        ctrl['ver_AML_int'], ctrl['ver_AML_str']))
    slist.append('MAME version           {:,} [COLOR violet]{}[/COLOR]'.format(
        ctrl['ver_mame_int'], ctrl['ver_mame_str']))
    slist.append('Operation mode         [COLOR violet]{:s}[/COLOR]'.format(settings['op_mode']))
    slist.append('Software Lists         [COLOR violet]{:s}[/COLOR]'.format(SL_str))
    # Information in the MAME XML control file.
    if XML_ctrl_dic['t_XML_extraction']:
        slist.append('XML extraction time    {}'.format(misc_time_to_str(XML_ctrl_dic['t_XML_extraction'])))
    else:
        slist.append('XML extraction time    {}'.format('no extracted'))
    if XML_ctrl_dic['st_mtime']:
        slist.append('XML modification time  {}'.format(misc_time_to_str(XML_ctrl_dic['st_mtime'])))
    else:
        slist.append('XML extraction time    {}'.format('undefined'))
    if XML_ctrl_dic['t_XML_preprocessing']:
        slist.append('XML preprocess time    {}'.format(misc_time_to_str(XML_ctrl_dic['t_XML_preprocessing'])))
    else:
        slist.append('XML extraction time    {}'.format('undefined'))
    slist.append('XML size               {:,} bytes'.format(XML_ctrl_dic['st_size']))
    slist.append('XML machine count      {:,} machines'.format(XML_ctrl_dic['total_machines']))

    slist.append('')
    slist.append('[COLOR orange]MAME machine count[/COLOR]')
    table_str = []
    table_str.append(['left', 'right', 'right',  'right'])
    table_str.append(['Type', 'Total', 'Parent', 'Clones'])
    table_str.append([
        'Machines',
        '{:6,d}'.format(control_dic['stats_processed_machines']),
        '{:6,d}'.format(control_dic['stats_parents']),
        '{:6,d}'.format(control_dic['stats_clones']),
    ])
    table_str.append([
        'Runnable',
        '{:6,d}'.format(control_dic['stats_runnable']),
        '{:6,d}'.format(control_dic['stats_runnable_parents']),
        '{:6,d}'.format(control_dic['stats_runnable_clones']),
    ])
    table_str.append([
        'Coin',
        '{:6,d}'.format(control_dic['stats_coin']),
        '{:6,d}'.format(control_dic['stats_coin_parents']),
        '{:6,d}'.format(control_dic['stats_coin_clones']),
    ])
    table_str.append([
        'Nocoin',
        '{:6,d}'.format(control_dic['stats_nocoin']),
        '{:6,d}'.format(control_dic['stats_nocoin_parents']),
        '{:6,d}'.format(control_dic['stats_nocoin_clones']),
    ])
    table_str.append([
        'Mechanical',
        '{:6,d}'.format(control_dic['stats_mechanical']),
        '{:6,d}'.format(control_dic['stats_mechanical_parents']),
        '{:6,d}'.format(control_dic['stats_mechanical_clones']),
    ])
    table_str.append([
        'Dead',
        '{:6,d}'.format(control_dic['stats_dead']),
        '{:6,d}'.format(control_dic['stats_dead_parents']),
        '{:6,d}'.format(control_dic['stats_dead_clones']),
    ])
    table_str.append([
        'Devices',
        '{:6,d}'.format(control_dic['stats_devices']),
        '{:6,d}'.format(control_dic['stats_devices_parents']),
        '{:6,d}'.format(control_dic['stats_devices_clones']),
    ])
    # Binary filters
    table_str.append([
        'BIOS',
        '{:6,d}'.format(control_dic['stats_BIOS']),
        '{:6,d}'.format(control_dic['stats_BIOS_parents']),
        '{:6,d}'.format(control_dic['stats_BIOS_clones']),
    ])
    table_str.append([
        'Samples',
        '{:6,d}'.format(control_dic['stats_samples']),
        '{:6,d}'.format(control_dic['stats_samples_parents']),
        '{:6,d}'.format(control_dic['stats_samples_clones']),
    ])
    slist.extend(text_render_table(table_str))

    slist.append('')
    slist.append('[COLOR orange]MAME machine statistics[/COLOR]')
    table_str = []
    table_str.append(['left', 'right', 'right', 'right', 'right', 'right', 'right', 'right', 'right'])
    table_str.append(['Type (parents/total)', 'Total', '', 'Good', '', 'Imperfect', '', 'Nonworking', ''])
    table_str.append(['Coin slot (Normal)',
        '{:,}'.format(control_dic['stats_MF_Normal_Total_parents']),
        '{:,}'.format(control_dic['stats_MF_Normal_Total']),
        '{:,}'.format(control_dic['stats_MF_Normal_Good_parents']),
        '{:,}'.format(control_dic['stats_MF_Normal_Good']),
        '{:,}'.format(control_dic['stats_MF_Normal_Imperfect_parents']),
        '{:,}'.format(control_dic['stats_MF_Normal_Imperfect']),
        '{:,}'.format(control_dic['stats_MF_Normal_Nonworking_parents']),
        '{:,}'.format(control_dic['stats_MF_Normal_Nonworking']),
    ])
    table_str.append(['Coin slot (Unusual)',
        '{:,}'.format(control_dic['stats_MF_Unusual_Total_parents']),
        '{:,}'.format(control_dic['stats_MF_Unusual_Total']),
        '{:,}'.format(control_dic['stats_MF_Unusual_Good_parents']),
        '{:,}'.format(control_dic['stats_MF_Unusual_Good']),
        '{:,}'.format(control_dic['stats_MF_Unusual_Imperfect_parents']),
        '{:,}'.format(control_dic['stats_MF_Unusual_Imperfect']),
        '{:,}'.format(control_dic['stats_MF_Unusual_Nonworking_parents']),
        '{:,}'.format(control_dic['stats_MF_Unusual_Nonworking']),
    ])
    table_str.append(['No coin slot',
        '{:,}'.format(control_dic['stats_MF_Nocoin_Total_parents']),
        '{:,}'.format(control_dic['stats_MF_Nocoin_Total']),
        '{:,}'.format(control_dic['stats_MF_Nocoin_Good_parents']),
        '{:,}'.format(control_dic['stats_MF_Nocoin_Good']),
        '{:,}'.format(control_dic['stats_MF_Nocoin_Imperfect_parents']),
        '{:,}'.format(control_dic['stats_MF_Nocoin_Imperfect']),
        '{:,}'.format(control_dic['stats_MF_Nocoin_Nonworking_parents']),
        '{:,}'.format(control_dic['stats_MF_Nocoin_Nonworking']),
    ])
    table_str.append(['Mechanical machines',
        '{:,}'.format(control_dic['stats_MF_Mechanical_Total_parents']),
        '{:,}'.format(control_dic['stats_MF_Mechanical_Total']),
        '{:,}'.format(control_dic['stats_MF_Mechanical_Good_parents']),
        '{:,}'.format(control_dic['stats_MF_Mechanical_Good']),
        '{:,}'.format(control_dic['stats_MF_Mechanical_Imperfect_parents']),
        '{:,}'.format(control_dic['stats_MF_Mechanical_Imperfect']),
        '{:,}'.format(control_dic['stats_MF_Mechanical_Nonworking_parents']),
        '{:,}'.format(control_dic['stats_MF_Mechanical_Nonworking']),
    ])
    table_str.append(['Dead machines',
        '{:,}'.format(control_dic['stats_MF_Dead_Total_parents']),
        '{:,}'.format(control_dic['stats_MF_Dead_Total']),
        '{:,}'.format(control_dic['stats_MF_Dead_Good_parents']),
        '{:,}'.format(control_dic['stats_MF_Dead_Good']),
        '{:,}'.format(control_dic['stats_MF_Dead_Imperfect_parents']),
        '{:,}'.format(control_dic['stats_MF_Dead_Imperfect']),
        '{:,}'.format(control_dic['stats_MF_Dead_Nonworking_parents']),
        '{:,}'.format(control_dic['stats_MF_Dead_Nonworking']),
    ])
    table_str.append(['Device machines',
        '{:,}'.format(control_dic['stats_devices_parents']),
        '{:,}'.format(control_dic['stats_devices']),
        'N/A', 'N/A', 'N/A', 'N/A', 'N/A', 'N/A'])
    slist.extend(text_render_table(table_str))

    if settings['global_enable_SL']:
        slist.append('\n[COLOR orange]Software Lists item count[/COLOR]')
        slist.append("SL XML files        {:7,d}".format(control_dic['stats_SL_XML_files']))
        slist.append("SL software items   {:7,d}".format(control_dic['stats_SL_software_items']))
        slist.append("SL items with ROMs  {:7,d}".format(control_dic['stats_SL_items_with_ROMs']))
        slist.append("SL items with CHDs  {:7,d}".format(control_dic['stats_SL_items_with_CHDs']))

def mame_stats_scanner_print_slist(cfg, slist, control_dic):
    settings = cfg.settings
    # MAME statistics
    slist.append('[COLOR orange]MAME scanner information[/COLOR]')
    t_str = [
        ['left', 'right', 'right',  'right'],
        ['Stat', 'Total', 'Have', 'Missing'],
        ['ROM ZIP files',
            '{:,}'.format(control_dic['scan_ROM_ZIP_files_total']),
            '{:,}'.format(control_dic['scan_ROM_ZIP_files_have']),
            '{:,}'.format(control_dic['scan_ROM_ZIP_files_missing'])],
        ['Sample ZIP files',
            '{:,}'.format(control_dic['scan_Samples_ZIP_total']),
            '{:,}'.format(control_dic['scan_Samples_ZIP_have']),
            '{:,}'.format(control_dic['scan_Samples_ZIP_missing'])],
        ['CHD files',
            '{:,}'.format(control_dic['scan_CHD_files_total']),
            '{:,}'.format(control_dic['scan_CHD_files_have']),
            '{:,}'.format(control_dic['scan_CHD_files_missing'])],
    ]
    slist.extend(text_render_table(t_str))

    slist.append('')
    t_str = [
        ['left', 'right', 'right',  'right'],
        ['Stat', 'Can run', 'Out of', 'Unrunnable'],
    ]
    t_str.append(['ROM machines',
        '{:,}'.format(control_dic['scan_machine_archives_ROM_have']),
        '{:,}'.format(control_dic['scan_machine_archives_ROM_total']),
        '{:,}'.format(control_dic['scan_machine_archives_ROM_missing']),
    ])
    t_str.append(['Sample machines',
        '{:,}'.format(control_dic['scan_machine_archives_Samples_have']),
        '{:,}'.format(control_dic['scan_machine_archives_Samples_total']),
        '{:,}'.format(control_dic['scan_machine_archives_Samples_missing']),
    ])
    t_str.append(['CHD machines',
        '{:,}'.format(control_dic['scan_machine_archives_CHD_have']),
        '{:,}'.format(control_dic['scan_machine_archives_CHD_total']),
        '{:,}'.format(control_dic['scan_machine_archives_CHD_missing']),
    ])
    slist.extend(text_render_table(t_str))

    # SL scanner statistics
    if settings['global_enable_SL']:
        slist.append('')
        slist.append('[COLOR orange]Software List scanner information[/COLOR]')
        t_str = [
            ['left', 'right', 'right',  'right'],
            ['Stat', 'Total', 'Have', 'Missing'],
        ]
        t_str.append(['SL ROMs',
            '{:,}'.format(control_dic['scan_SL_archives_ROM_total']),
            '{:,}'.format(control_dic['scan_SL_archives_ROM_have']),
            '{:,}'.format(control_dic['scan_SL_archives_ROM_missing']),
        ])
        t_str.append(['SL CHDs',
            '{:,}'.format(control_dic['scan_SL_archives_CHD_total']),
            '{:,}'.format(control_dic['scan_SL_archives_CHD_have']),
            '{:,}'.format(control_dic['scan_SL_archives_CHD_missing']),
        ])
        slist.extend(text_render_table(t_str))

    # --- MAME asset scanner ---
    slist.append('')
    slist.append('[COLOR orange]MAME asset scanner information[/COLOR]')
    # slist.append('Total number of MAME machines {0:,d}'.format(control_dic['assets_num_MAME_machines']))
    t_str = [
        ['left', 'right', 'right',  'right'],
        ['Stat', 'Have', 'Missing', 'Alternate'],
    ]
    t_str.append(['3D Boxes',
        '{:,}'.format(control_dic['assets_3dbox_have']),
        '{:,}'.format(control_dic['assets_3dbox_missing']),
        '{:,}'.format(control_dic['assets_3dbox_alternate']),
    ])
    t_str.append(['Artpreviews',
        '{:,}'.format(control_dic['assets_artpreview_have']),
        '{:,}'.format(control_dic['assets_artpreview_missing']),
        '{:,}'.format(control_dic['assets_artpreview_alternate']),
    ])
    t_str.append(['Artwork',
        '{:,}'.format(control_dic['assets_artwork_have']),
        '{:,}'.format(control_dic['assets_artwork_missing']),
        '{:,}'.format(control_dic['assets_artwork_alternate']),
    ])
    t_str.append(['Cabinets',
        '{:,}'.format(control_dic['assets_cabinets_have']),
        '{:,}'.format(control_dic['assets_cabinets_missing']),
        '{:,}'.format(control_dic['assets_cabinets_alternate']),
    ])
    t_str.append(['Clearlogos',
        '{:,}'.format(control_dic['assets_clearlogos_have']),
        '{:,}'.format(control_dic['assets_clearlogos_missing']),
        '{:,}'.format(control_dic['assets_clearlogos_alternate']),
    ])
    t_str.append(['CPanels',
        '{:,}'.format(control_dic['assets_cpanels_have']),
        '{:,}'.format(control_dic['assets_cpanels_missing']),
        '{:,}'.format(control_dic['assets_cpanels_alternate']),
    ])
    t_str.append(['Fanart',
        '{:,}'.format(control_dic['assets_fanarts_have']),
        '{:,}'.format(control_dic['assets_fanarts_missing']),
        '{:,}'.format(control_dic['assets_fanarts_alternate']),
    ])
    t_str.append(['Flyers',
        '{:,}'.format(control_dic['assets_flyers_have']),
        '{:,}'.format(control_dic['assets_flyers_missing']),
        '{:,}'.format(control_dic['assets_flyers_alternate']),
    ])
    t_str.append(['Manuals',
        '{:,}'.format(control_dic['assets_manuals_have']),
        '{:,}'.format(control_dic['assets_manuals_missing']),
        '{:,}'.format(control_dic['assets_manuals_alternate']),
    ])
    t_str.append(['Marquees',
        '{:,}'.format(control_dic['assets_marquees_have']),
        '{:,}'.format(control_dic['assets_marquees_missing']),
        '{:,}'.format(control_dic['assets_marquees_alternate']),
    ])
    t_str.append(['PCBs',
        '{:,}'.format(control_dic['assets_PCBs_have']),
        '{:,}'.format(control_dic['assets_PCBs_missing']),
        '{:,}'.format(control_dic['assets_PCBs_alternate']),
    ])
    t_str.append(['Snaps',
        '{:,}'.format(control_dic['assets_snaps_have']),
        '{:,}'.format(control_dic['assets_snaps_missing']),
        '{:,}'.format(control_dic['assets_snaps_alternate']),
    ])
    t_str.append(['Titles',
        '{:,}'.format(control_dic['assets_titles_have']),
        '{:,}'.format(control_dic['assets_titles_missing']),
        '{:,}'.format(control_dic['assets_titles_alternate']),
    ])
    t_str.append(['Trailers',
        '{:,}'.format(control_dic['assets_trailers_have']),
        '{:,}'.format(control_dic['assets_trailers_missing']),
        '{:,}'.format(control_dic['assets_trailers_alternate']),
    ])
    slist.extend(text_render_table(t_str))

    # --- Software List scanner ---
    if settings['global_enable_SL']:
        slist.append('')
        slist.append('[COLOR orange]Software List asset scanner information[/COLOR]')
        # slist.append('Total number of SL items {0:,d}'.format(control_dic['assets_SL_num_items']))
        t_str = [
            ['left', 'right', 'right',  'right'],
            ['Stat', 'Have', 'Missing', 'Alternate'],
        ]
        t_str.append(['3D Boxes',
            '{:,}'.format(control_dic['assets_SL_3dbox_have']),
            '{:,}'.format(control_dic['assets_SL_3dbox_missing']),
            '{:,}'.format(control_dic['assets_SL_3dbox_alternate']),
        ])
        t_str.append(['Titles',
            '{:,}'.format(control_dic['assets_SL_titles_have']),
            '{:,}'.format(control_dic['assets_SL_titles_missing']),
            '{:,}'.format(control_dic['assets_SL_titles_alternate']),
        ])
        t_str.append(['Snaps',
            '{:,}'.format(control_dic['assets_SL_snaps_have']),
            '{:,}'.format(control_dic['assets_SL_snaps_missing']),
            '{:,}'.format(control_dic['assets_SL_snaps_alternate']),
        ])
        t_str.append(['Boxfronts',
            '{:,}'.format(control_dic['assets_SL_boxfronts_have']),
            '{:,}'.format(control_dic['assets_SL_boxfronts_missing']),
            '{:,}'.format(control_dic['assets_SL_boxfronts_alternate']),
        ])
        t_str.append(['Fanarts',
            '{:,}'.format(control_dic['assets_SL_fanarts_have']),
            '{:,}'.format(control_dic['assets_SL_fanarts_missing']),
            '{:,}'.format(control_dic['assets_SL_fanarts_alternate']),
        ])
        t_str.append(['Trailers',
            '{:,}'.format(control_dic['assets_SL_trailers_have']),
            '{:,}'.format(control_dic['assets_SL_trailers_missing']),
            '{:,}'.format(control_dic['assets_SL_trailers_alternate']),
        ])
        t_str.append(['Manuals',
            '{:,}'.format(control_dic['assets_SL_manuals_have']),
            '{:,}'.format(control_dic['assets_SL_manuals_missing']),
            '{:,}'.format(control_dic['assets_SL_manuals_alternate']),
        ])
        slist.extend(text_render_table(t_str))

def mame_stats_audit_print_slist(cfg, slist, control_dic):
    settings = cfg.settings
    rom_set = ['Merged', 'Split', 'Non-merged'][settings['mame_rom_set']]
    chd_set = ['Merged', 'Split', 'Non-merged'][settings['mame_chd_set']]

    slist.append('[COLOR orange]MAME ROM audit database statistics[/COLOR]')
    t = "{:7,d} runnable MAME machines"
    slist.append(t.format(control_dic['stats_audit_MAME_machines_runnable']))
    t = "{:7,d} machines require ROM ZIPs, {:7,d} parents and {:7,d} clones"
    slist.append(t.format(control_dic['stats_audit_machine_archives_ROM'],
                          control_dic['stats_audit_machine_archives_ROM_parents'],
                          control_dic['stats_audit_machine_archives_ROM_clones']))
    t = "{:7,d} machines require CHDs,     {:7,d} parents and {:7,d} clones"
    slist.append(t.format(control_dic['stats_audit_machine_archives_CHD'],
                          control_dic['stats_audit_machine_archives_CHD_parents'],
                          control_dic['stats_audit_machine_archives_CHD_clones']))
    t = "{:7,d} machines require Samples,  {:7,d} parents and {:7,d} clones"
    slist.append(t.format(control_dic['stats_audit_machine_archives_Samples'],
                          control_dic['stats_audit_machine_archives_Samples_parents'],
                          control_dic['stats_audit_machine_archives_Samples_clones']))
    t = "{:7,d} machines require nothing,  {:7,d} parents and {:7,d} clones"
    slist.append(t.format(control_dic['stats_audit_archive_less'],
                          control_dic['stats_audit_archive_less_parents'],
                          control_dic['stats_audit_archive_less_clones']))

    t = "{:7,d} ROM ZIPs in the [COLOR darkorange]{}[/COLOR] set"
    slist.append(t.format(control_dic['stats_audit_MAME_ROM_ZIP_files'], rom_set))
    t = "{:7,d} CHDs in the [COLOR darkorange]{}[/COLOR] set"
    slist.append(t.format(control_dic['stats_audit_MAME_CHD_files'], chd_set))
    t = "{:7,d} Sample ZIPs in the [COLOR darkorange]{}[/COLOR] set"
    slist.append(t.format(control_dic['stats_audit_MAME_Sample_ZIP_files'], rom_set))

    t = "{:7,d} total ROMs, {:7,d} valid and {:7,d} invalid"
    slist.append(t.format(
        control_dic['stats_audit_ROMs_total'],
        control_dic['stats_audit_ROMs_valid'],
        control_dic['stats_audit_ROMs_invalid'],
    ))
    t = "{:7,d} total CHDs, {:7,d} valid and {:7,d} invalid"
    slist.append(t.format(
        control_dic['stats_audit_CHDs_total'],
        control_dic['stats_audit_CHDs_valid'],
        control_dic['stats_audit_CHDs_invalid'],
    ))

    # SL item audit database statistics
    if settings['global_enable_SL']:
        slist.append('\n[COLOR orange]SL audit database statistics[/COLOR]')
        t = "{:7,d} runnable Software List items"
        slist.append(t.format(control_dic['stats_audit_SL_items_runnable']))
        t = "{:7,d} SL items require ROM ZIPs and/or CHDs"
        slist.append(t.format(control_dic['stats_audit_SL_items_with_arch']))
        t = "{:7,d} SL items require ROM ZIPs"
        slist.append(t.format(control_dic['stats_audit_SL_items_with_arch_ROM']))
        t = "{:7,d} SL items require CHDs"
        slist.append(t.format(control_dic['stats_audit_SL_items_with_CHD']))

    # MAME audit summary.
    slist.append('\n[COLOR orange]MAME ROM audit information[/COLOR]')
    table_str = [
        ['left', 'right', 'right', 'right'],
        ['Type', 'Total', 'Good', 'Bad'],
    ]
    table_str.append([
        'Machines with ROMs and/or CHDs',
        '{:,d}'.format(control_dic['audit_MAME_machines_with_arch']),
        '{:,d}'.format(control_dic['audit_MAME_machines_with_arch_OK']),
        '{:,d}'.format(control_dic['audit_MAME_machines_with_arch_BAD']),
    ])
    table_str.append([
        'Machines with ROMs',
        '{:,d}'.format(control_dic['audit_MAME_machines_with_ROMs']),
        '{:,d}'.format(control_dic['audit_MAME_machines_with_ROMs_OK']),
        '{:,d}'.format(control_dic['audit_MAME_machines_with_ROMs_BAD']),
    ])
    table_str.append([
        'Machines with CHDs',
        '{:,d}'.format(control_dic['audit_MAME_machines_with_CHDs']),
        '{:,d}'.format(control_dic['audit_MAME_machines_with_CHDs_OK']),
        '{:,d}'.format(control_dic['audit_MAME_machines_with_CHDs_BAD']),
    ])
    table_str.append([
        'Machines with Samples',
        '{:,d}'.format(control_dic['audit_MAME_machines_with_SAMPLES']),
        '{:,d}'.format(control_dic['audit_MAME_machines_with_SAMPLES_OK']),
        '{:,d}'.format(control_dic['audit_MAME_machines_with_SAMPLES_BAD']),
    ])
    slist.extend(text_render_table(table_str))

    # SL audit summary.
    if settings['global_enable_SL']:
        slist.append('\n[COLOR orange]SL audit information[/COLOR]')
        table_str = [
            ['left', 'right', 'right', 'right'],
            ['Type', 'Total', 'Good', 'Bad'],
        ]
        table_str.append([
            'SL items with ROMs and/or CHDs',
            '{:,d}'.format(control_dic['audit_SL_items_with_arch']),
            '{:,d}'.format(control_dic['audit_SL_items_with_arch_OK']),
            '{:,d}'.format(control_dic['audit_SL_items_with_arch_BAD']),
        ])
        table_str.append([
            'SL items with ROMs',
            '{:,d}'.format(control_dic['audit_SL_items_with_arch_ROM']),
            '{:,d}'.format(control_dic['audit_SL_items_with_arch_ROM_OK']),
            '{:,d}'.format(control_dic['audit_SL_items_with_arch_ROM_BAD']),
        ])
        table_str.append([
            'SL items with CHDs',
            '{:,d}'.format(control_dic['audit_SL_items_with_CHD']),
            '{:,d}'.format(control_dic['audit_SL_items_with_CHD_OK']),
            '{:,d}'.format(control_dic['audit_SL_items_with_CHD_BAD']),
        ])
        slist.extend(text_render_table(table_str))

def mame_stats_timestamps_slist(cfg, slist, control_dic):
    settings = cfg.settings
    # DAT/INI file versions. Note than in some DAT/INIs the version is not available.
    slist.append('[COLOR orange]DAT/INI versions[/COLOR]')
    slist.append("Alltime.ini version   {}".format(control_dic['ver_alltime']))
    slist.append("Artwork.ini version   {}".format(control_dic['ver_artwork']))
    slist.append("bestgames.ini version {}".format(control_dic['ver_bestgames']))
    slist.append("Category.ini version  {}".format(control_dic['ver_category']))
    slist.append("catlist.ini version   {}".format(control_dic['ver_catlist']))
    slist.append("catver.ini version    {}".format(control_dic['ver_catver']))
    slist.append("command.dat version   {}".format(control_dic['ver_command']))
    slist.append("gameinit.dat version  {}".format(control_dic['ver_gameinit']))
    slist.append("genre.ini version     {}".format(control_dic['ver_genre']))
    slist.append("history.dat version   {}".format(control_dic['ver_history']))
    slist.append("mameinfo.dat version  {}".format(control_dic['ver_mameinfo']))
    slist.append("mature.ini version    {}".format(control_dic['ver_mature']))
    slist.append("nplayers.ini version  {}".format(control_dic['ver_nplayers']))
    slist.append("series.ini version    {}".format(control_dic['ver_series']))

    # Timestamps ordered if user selects "All in one step"
    slist.append('')
    slist.append('[COLOR orange]Timestamps[/COLOR]')
    # MAME and SL databases.
    if control_dic['t_MAME_DB_build']:
        slist.append("MAME DB built on            {}".format(misc_time_to_str(control_dic['t_MAME_DB_build'])))
    else:
        slist.append("MAME DB never built")
    if control_dic['t_MAME_Audit_DB_build']:
        slist.append("MAME Audit DB built on      {}".format(misc_time_to_str(control_dic['t_MAME_Audit_DB_build'])))
    else:
        slist.append("MAME Audit DB never built")
    if control_dic['t_MAME_Catalog_build']:
        slist.append("MAME Catalog built on       {}".format(misc_time_to_str(control_dic['t_MAME_Catalog_build'])))
    else:
        slist.append("MAME Catalog never built")
    if control_dic['t_SL_DB_build']:
        slist.append("SL DB built on              {}".format(misc_time_to_str(control_dic['t_SL_DB_build'])))
    else:
        slist.append("SL DB never built")

    # MAME and SL scanner.
    if control_dic['t_MAME_ROMs_scan']:
        slist.append("MAME ROMs scaned on         {}".format(misc_time_to_str(control_dic['t_MAME_ROMs_scan'])))
    else:
        slist.append("MAME ROMs never scaned")
    if control_dic['t_MAME_assets_scan']:
        slist.append("MAME assets scaned on       {}".format(misc_time_to_str(control_dic['t_MAME_assets_scan'])))
    else:
        slist.append("MAME assets never scaned")

    if control_dic['t_SL_ROMs_scan']:
        slist.append("SL ROMs scaned on           {}".format(misc_time_to_str(control_dic['t_SL_ROMs_scan'])))
    else:
        slist.append("SL ROMs never scaned")
    if control_dic['t_SL_assets_scan']:
        slist.append("SL assets scaned on         {}".format(misc_time_to_str(control_dic['t_SL_assets_scan'])))
    else:
        slist.append("SL assets never scaned")

    # Plots, Fanarts and 3D Boxes.
    if control_dic['t_MAME_plots_build']:
        slist.append("MAME Plots built on         {}".format(misc_time_to_str(control_dic['t_MAME_plots_build'])))
    else:
        slist.append("MAME Plots never built")
    if control_dic['t_SL_plots_build']:
        slist.append("SL Plots built on           {}".format(misc_time_to_str(control_dic['t_SL_plots_build'])))
    else:
        slist.append("SL Plots never built")

    if control_dic['t_MAME_fanart_build']:
        slist.append("MAME Fanarts built on       {}".format(misc_time_to_str(control_dic['t_MAME_fanart_build'])))
    else:
        slist.append("MAME Fanarts never built")
    if control_dic['t_SL_fanart_build']:
        slist.append("SL Fanarts built on         {}".format(misc_time_to_str(control_dic['t_SL_fanart_build'])))
    else:
        slist.append("SL Fanarts never built")

    if control_dic['t_MAME_3dbox_build']:
        slist.append("MAME 3D Boxes built on      {}".format(misc_time_to_str(control_dic['t_MAME_3dbox_build'])))
    else:
        slist.append("MAME 3D Boxes never built")
    if control_dic['t_SL_3dbox_build']:
        slist.append("SL 3D Boxes built on        {}".format(misc_time_to_str(control_dic['t_SL_3dbox_build'])))
    else:
        slist.append("SL 3D Boxes never built")

    # MAME machine hash, asset hash, render cache and asset cache.
    if control_dic['t_MAME_machine_hash']:
        slist.append("MAME machine hash built on  {}".format(misc_time_to_str(control_dic['t_MAME_machine_hash'])))
    else:
        slist.append("MAME machine hash never built")
    if control_dic['t_MAME_asset_hash']:
        slist.append("MAME asset hash built on    {}".format(misc_time_to_str(control_dic['t_MAME_asset_hash'])))
    else:
        slist.append("MAME asset hash never built")
    if control_dic['t_MAME_render_cache_build']:
        slist.append("MAME render cache built on  {}".format(misc_time_to_str(control_dic['t_MAME_render_cache_build'])))
    else:
        slist.append("MAME render cache never built")
    if control_dic['t_MAME_asset_cache_build']:
        slist.append("MAME asset cache built on   {}".format(misc_time_to_str(control_dic['t_MAME_asset_cache_build'])))
    else:
        slist.append("MAME asset cache never built")

    # Custsom filters.
    if control_dic['t_Custom_Filter_build']:
        slist.append("Custom filters built on     {}".format(misc_time_to_str(control_dic['t_Custom_Filter_build'])))
    else:
        slist.append("Custom filters never built")

    # Audit stuff.
    if control_dic['t_MAME_audit']:
        slist.append("MAME ROMs audited on        {}".format(misc_time_to_str(control_dic['t_MAME_audit'])))
    else:
        slist.append("MAME ROMs never audited")
    if control_dic['t_SL_audit']:
        slist.append("SL ROMs audited on          {}".format(misc_time_to_str(control_dic['t_SL_audit'])))
    else:
        slist.append("SL ROMs never audited")

# -------------------------------------------------------------------------------------------------
# Check/Update/Repair Favourite ROM objects
# -------------------------------------------------------------------------------------------------
def mame_update_MAME_Fav_objects(cfg, db_dic):
    control_dic = db_dic['control_dic']
    machines = db_dic['machines']
    renderdb_dic = db_dic['renderdb']
    assets_dic = db_dic['assetdb']
    fav_machines = utils_load_JSON_file(cfg.FAV_MACHINES_PATH.getPath())
    # If no MAME Favourites return
    if len(fav_machines) < 1:
        kodi_notify('MAME Favourites empty')
        return
    iteration = 0
    d_text = 'Checking/Updating MAME Favourites...'
    pDialog = KodiProgressDialog()
    pDialog.startProgress(d_text, len(fav_machines))
    for fav_key in sorted(fav_machines):
        log_debug('Checking machine "{}"'.format(fav_key))
        if fav_key in machines:
            machine = machines[fav_key]
            render = renderdb_dic[fav_key]
            assets = assets_dic[fav_key]
        else:
            # Machine not found in DB. Create an empty one to update the database fields.
            # The user can delete it later.
            log_debug('Machine "{}" not found in MAME main DB'.format(fav_key))
            machine = db_new_machine_dic()
            render = db_new_machine_render_dic()
            assets = db_new_MAME_asset()
            # Change plot to warn user this machine is not found in database.
            t = 'Machine {} missing'.format(fav_key)
            render['description'] = t
            assets['plot'] = t
        new_fav = db_get_MAME_Favourite_full(fav_key, machine, render, assets, control_dic)
        fav_machines[fav_key] = new_fav
        log_debug('Updated machine "{}"'.format(fav_key))
        iteration += 1
        pDialog.updateProgress(iteration)
    utils_write_JSON_file(cfg.FAV_MACHINES_PATH.getPath(), fav_machines)
    pDialog.endProgress()

def mame_update_MAME_MostPlay_objects(cfg, db_dic):
    control_dic = db_dic['control_dic']
    machines = db_dic['machines']
    renderdb_dic = db_dic['renderdb']
    assets_dic = db_dic['assetdb']
    most_played_roms_dic = utils_load_JSON_file(cfg.MAME_MOST_PLAYED_FILE_PATH.getPath())
    if len(most_played_roms_dic) < 1:
        kodi_notify('MAME Most Played empty')
        return
    iteration = 0
    pDialog = KodiProgressDialog()
    pDialog.startProgress('Checking/Updating MAME Most Played machines...', len(most_played_roms_dic))
    for fav_key in sorted(most_played_roms_dic):
        log_debug('Checking machine "{}"'.format(fav_key))
        if 'launch_count' in most_played_roms_dic[fav_key]:
            launch_count = most_played_roms_dic[fav_key]['launch_count']
        else:
            launch_count = 1
        if fav_key in machines:
            machine = machines[fav_key]
            render = renderdb_dic[fav_key]
            assets = assets_dic[fav_key]
        else:
            log_debug('Machine "{}" not found in MAME main DB'.format(fav_key))
            machine = db_new_machine_dic()
            render = db_new_machine_render_dic()
            assets = db_new_MAME_asset()
            t = 'Machine {} missing'.format(fav_key)
            render['description'] = t
            assets['plot'] = t
        new_fav = db_get_MAME_Favourite_full(fav_key, machine, render, assets, control_dic)
        new_fav['launch_count'] = launch_count
        most_played_roms_dic[fav_key] = new_fav
        log_debug('Updated machine "{}"'.format(fav_key))
        iteration += 1
        pDialog.updateProgress(iteration)
    utils_write_JSON_file(cfg.MAME_MOST_PLAYED_FILE_PATH.getPath(), most_played_roms_dic)
    pDialog.endProgress()

def mame_update_MAME_RecentPlay_objects(cfg, db_dic):
    control_dic = db_dic['control_dic']
    machines = db_dic['machines']
    renderdb_dic = db_dic['renderdb']
    assets_dic = db_dic['assetdb']
    recent_roms_list = utils_load_JSON_file(cfg.MAME_RECENT_PLAYED_FILE_PATH.getPath(), [])
    if len(recent_roms_list) < 1:
        kodi_notify('MAME Recently Played empty')
        return
    iteration = 0
    pDialog = KodiProgressDialog()
    pDialog.startProgress('Checking/Updating MAME Recently Played machines...', len(recent_roms_list))
    for i, recent_rom in enumerate(recent_roms_list):
        fav_key = recent_rom['name']
        log_debug('Checking machine "{}"'.format(fav_key))
        if fav_key in machines:
            machine = machines[fav_key]
            render = renderdb_dic[fav_key]
            assets = assets_dic[fav_key]
        else:
            log_debug('Machine "{}" not found in MAME main DB'.format(fav_key))
            machine = db_new_machine_dic()
            render = db_new_machine_render_dic()
            assets = db_new_MAME_asset()
            t = 'Machine {} missing'.format(fav_key)
            render['description'] = t
            assets['plot'] = t
        new_fav = db_get_MAME_Favourite_full(fav_key, machine, render, assets, control_dic)
        recent_roms_list[i] = new_fav
        log_debug('Updated machine "{}"'.format(fav_key))
        iteration += 1
        pDialog.updateProgress(iteration)
    utils_write_JSON_file(cfg.MAME_RECENT_PLAYED_FILE_PATH.getPath(), recent_roms_list)
    pDialog.endProgress()

def mame_update_SL_Fav_objects(cfg, db_dic):
    control_dic = db_dic['control_dic']
    SL_index = db_dic['SL_index']
    pDialog = KodiProgressDialog()
    pDialog.startProgress('Loading SL Most Played JSON DB...')
    fav_SL_roms = utils_load_JSON_file(cfg.FAV_SL_ROMS_PATH.getPath())
    if len(fav_SL_roms) < 1:
        kodi_notify_warn('SL Most Played empty')
        return
    pDialog.resetProgress('Checking SL Favourites', len(fav_SL_roms))
    for fav_SL_key in sorted(fav_SL_roms):
        if 'ROM_name' in fav_SL_roms[fav_SL_key]:
            fav_ROM_name = fav_SL_roms[fav_SL_key]['ROM_name']
        elif 'SL_ROM_name' in fav_SL_roms[fav_SL_key]:
            fav_ROM_name = fav_SL_roms[fav_SL_key]['SL_ROM_name']
        else:
            raise TypeError('Cannot find SL ROM name')
        fav_SL_name = fav_SL_roms[fav_SL_key]['SL_name']
        log_debug('Checking SL Favourite "{}" / "{}"'.format(fav_SL_name, fav_ROM_name))
        pDialog.updateProgressInc('Checking SL Favourites...\nItem "{}"'.format(fav_ROM_name))

        # --- Load SL ROMs DB and assets ---
        file_name =  SL_index[fav_SL_name]['rom_DB_noext'] + '_items.json'
        SL_DB_FN = cfg.SL_DB_DIR.pjoin(file_name)
        assets_file_name =  SL_index[fav_SL_name]['rom_DB_noext'] + '_assets.json'
        SL_asset_DB_FN = cfg.SL_DB_DIR.pjoin(assets_file_name)
        SL_roms = utils_load_JSON_file(SL_DB_FN.getPath(), verbose = False)
        SL_assets_dic = utils_load_JSON_file(SL_asset_DB_FN.getPath(), verbose = False)

        # --- Check ---
        if fav_ROM_name in SL_roms:
            SL_ROM = SL_roms[fav_ROM_name]
            SL_assets = SL_assets_dic[fav_ROM_name]
        else:
            # Machine not found in DB. Create an empty one to update the database fields.
            # The user can delete it later.
            log_debug('Machine "{}" / "{}" not found in SL main DB'.format(fav_ROM_name, fav_SL_name))
            SL_ROM = db_new_SL_ROM()
            SL_assets = db_new_SL_asset()
            # Change plot to warn user this machine is not found in database.
            t = 'Item "{}" missing'.format(fav_ROM_name)
            SL_ROM['description'] = t
            SL_ROM['plot'] = t
        new_fav_ROM = db_get_SL_Favourite(fav_SL_name, fav_ROM_name, SL_ROM, SL_assets, control_dic)
        fav_SL_roms[fav_SL_key] = new_fav_ROM
        log_debug('Updated SL Favourite "{}" / "{}"'.format(fav_SL_name, fav_ROM_name))
    utils_write_JSON_file(cfg.FAV_SL_ROMS_PATH.getPath(), fav_SL_roms)
    pDialog.endProgress()

def mame_update_SL_MostPlay_objects(cfg, db_dic):
    control_dic = db_dic['control_dic']
    SL_index = db_dic['SL_index']
    pDialog = KodiProgressDialog()
    pDialog.startProgress('Loading SL Most Played JSON DB...')
    most_played_roms_dic = utils_load_JSON_file(cfg.SL_MOST_PLAYED_FILE_PATH.getPath())
    if len(most_played_roms_dic) < 1:
        kodi_notify_warn('SL Most Played empty')
        return
    pDialog.resetProgress('Checking SL Most Played', len(most_played_roms_dic))
    for fav_SL_key in sorted(most_played_roms_dic):
        if 'ROM_name' in most_played_roms_dic[fav_SL_key]:
            fav_ROM_name = most_played_roms_dic[fav_SL_key]['ROM_name']
        elif 'SL_ROM_name' in most_played_roms_dic[fav_SL_key]:
            fav_ROM_name = most_played_roms_dic[fav_SL_key]['SL_ROM_name']
        else:
            raise TypeError('Cannot find SL ROM name')
        if 'launch_count' in most_played_roms_dic[fav_SL_key]:
            launch_count = most_played_roms_dic[fav_SL_key]['launch_count']
        else:
            launch_count = 1
        fav_SL_name = most_played_roms_dic[fav_SL_key]['SL_name']
        log_debug('Checking SL Most Played "{}" / "{}"'.format(fav_SL_name, fav_ROM_name))

        # Update progress dialog.
        pDialog.updateProgressInc('Checking SL Most Played...\nItem "{}"'.format(fav_ROM_name))

        # --- Load SL ROMs DB and assets ---
        file_name = SL_index[fav_SL_name]['rom_DB_noext'] + '_items.json'
        SL_DB_FN = cfg.SL_DB_DIR.pjoin(file_name)
        assets_file_name =  SL_index[fav_SL_name]['rom_DB_noext'] + '_assets.json'
        SL_asset_DB_FN = cfg.SL_DB_DIR.pjoin(assets_file_name)
        SL_roms = utils_load_JSON_file(SL_DB_FN.getPath(), verbose = False)
        SL_assets_dic = utils_load_JSON_file(SL_asset_DB_FN.getPath(), verbose = False)

        # --- Check ---
        if fav_ROM_name in SL_roms:
            SL_ROM = SL_roms[fav_ROM_name]
            SL_assets = SL_assets_dic[fav_ROM_name]
        else:
            log_debug('Machine "{}" / "{}" not found in SL main DB'.format(fav_ROM_name, fav_SL_name))
            SL_ROM = db_new_SL_ROM()
            SL_assets = db_new_SL_asset()
            t = 'Item "{}" missing'.format(fav_ROM_name)
            SL_ROM['description'] = t
            SL_ROM['plot'] = t
        new_fav_ROM = db_get_SL_Favourite(fav_SL_name, fav_ROM_name, SL_ROM, SL_assets, control_dic)
        new_fav_ROM['launch_count'] = launch_count
        most_played_roms_dic[fav_SL_key] = new_fav_ROM
        log_debug('Updated SL Most Played "{}" / "{}"'.format(fav_SL_name, fav_ROM_name))
    utils_write_JSON_file(cfg.SL_MOST_PLAYED_FILE_PATH.getPath(), most_played_roms_dic)
    pDialog.endProgress()

def mame_update_SL_RecentPlay_objects(cfg, db_dic):
    control_dic = db_dic['control_dic']
    SL_index = db_dic['SL_index']
    pDialog = KodiProgressDialog()
    pDialog.startProgress('Loading SL Recently Played JSON DB...')
    recent_roms_list = utils_load_JSON_file(cfg.SL_RECENT_PLAYED_FILE_PATH.getPath(), [])
    if len(recent_roms_list) < 1:
        kodi_notify_warn('SL Recently Played empty')
        return
    pDialog.resetProgress('Checking SL Recently Played', len(recent_roms_list))
    for i, recent_rom in enumerate(recent_roms_list):
        if 'ROM_name' in recent_rom:
            fav_ROM_name = recent_rom['ROM_name']
        elif 'SL_ROM_name' in recent_rom:
            fav_ROM_name = recent_rom['SL_ROM_name']
        else:
            raise TypeError('Cannot find SL ROM name')
        fav_SL_name = recent_rom['SL_name']
        log_debug('Checking SL Recently Played "{}" / "{}"'.format(fav_SL_name, fav_ROM_name))
        pDialog.updateProgressInc('Checking SL Recently Played...\nItem "{}"'.format(fav_ROM_name))

        # --- Load SL ROMs DB and assets ---
        file_name = SL_index[fav_SL_name]['rom_DB_noext'] + '_items.json'
        SL_DB_FN = cfg.SL_DB_DIR.pjoin(file_name)
        assets_file_name =  SL_index[fav_SL_name]['rom_DB_noext'] + '_assets.json'
        SL_asset_DB_FN = cfg.SL_DB_DIR.pjoin(assets_file_name)
        SL_roms = utils_load_JSON_file(SL_DB_FN.getPath(), verbose = False)
        SL_assets_dic = utils_load_JSON_file(SL_asset_DB_FN.getPath(), verbose = False)

        # --- Check ---
        if fav_ROM_name in SL_roms:
            SL_ROM = SL_roms[fav_ROM_name]
            SL_assets = SL_assets_dic[fav_ROM_name]
        else:
            log_debug('Machine "{}" / "{}" not found in SL main DB'.format(fav_ROM_name, fav_SL_name))
            SL_ROM = db_new_SL_ROM()
            SL_assets = db_new_SL_asset()
            t = 'Item "{}" missing'.format(fav_ROM_name)
            SL_ROM['description'] = t
            SL_ROM['plot'] = t
        new_fav_ROM = db_get_SL_Favourite(fav_SL_name, fav_ROM_name, SL_ROM, SL_assets, control_dic)
        recent_roms_list[i] = new_fav_ROM
        log_debug('Updated SL Recently Played  "{}" / "{}"'.format(fav_SL_name, fav_ROM_name))
    utils_write_JSON_file(cfg.SL_RECENT_PLAYED_FILE_PATH.getPath(), recent_roms_list)
    pDialog.endProgress()

# ------------------------------------------------------------------------------------------------
# Build MAME and SL plots
# ------------------------------------------------------------------------------------------------

# Generate plot for MAME machines.
# Line 1) Controls are {Joystick}
# Line 2) {One Vertical Raster screen}
# Line 3) Machine [is|is not] mechanical and driver is neogeo.hpp
# Line 4) Machine has [no coin slots| N coin slots]
# Line 5) Artwork, Manual, History, Info, Gameinit, Command
# Line 6) Machine [supports|does not support] a Software List.
def mame_MAME_plot_slits(mname, m, assets_dic,
    history_info_set, mameinfo_info_set, gameinit_idx_dic, command_idx_dic):
    Flag_list = []
    if assets_dic[mname]['artwork']: Flag_list.append('Artwork')
    if assets_dic[mname]['manual']: Flag_list.append('Manual')
    if mname in history_info_set: Flag_list.append('History')
    if mname in mameinfo_info_set: Flag_list.append('Info')
    if mname in gameinit_idx_dic: Flag_list.append('Gameinit')
    if mname in command_idx_dic: Flag_list.append('Command')
    Flag_str = ', '.join(Flag_list)
    if m['input']:
        control_list = [ctrl_dic['type'] for ctrl_dic in m['input']['control_list']]
    else:
        control_list = []
    if control_list:
        controls_str = 'Controls {}'.format(misc_get_mame_control_str(control_list))
    else:
        controls_str = 'No controls'
    mecha_str = 'Mechanical' if m['isMechanical'] else 'Non-mechanical'
    n_coins = m['input']['att_coins'] if m['input'] else 0
    coin_str = 'Machine has {} coin slots'.format(n_coins) if n_coins > 0 else 'Machine has no coin slots'
    SL_str = ', '.join(m['softwarelists']) if m['softwarelists'] else ''

    plot_str_list = []
    plot_str_list.append('{}'.format(controls_str))
    plot_str_list.append('{}'.format(misc_get_mame_screen_str(mname, m)))
    plot_str_list.append('{} / Driver is {}'.format(mecha_str, m['sourcefile']))
    plot_str_list.append('{}'.format(coin_str))
    if Flag_str: plot_str_list.append('{}'.format(Flag_str))
    if SL_str: plot_str_list.append('SL {}'.format(SL_str))

    return plot_str_list

# Setting id="MAME_plot" values="Info|History DAT|Info + History DAT"
def mame_build_MAME_plots(cfg, db_dic_in):
    log_info('mame_build_MAME_plots() Building machine plots/descriptions ...')
    control_dic = db_dic_in['control_dic']
    machines = db_dic_in['machines']
    renderdb_dic = db_dic_in['renderdb']
    assetdb_dic = db_dic_in['assetdb']
    history_idx_dic = db_dic_in['history_idx_dic']
    mameinfo_idx_dic = db_dic_in['mameinfo_idx_dic']
    gameinit_idx_dic = db_dic_in['gameinit_idx_dic']
    command_idx_dic = db_dic_in['command_idx_dic']

    # Do not crash if DAT files are not configured.
    history_info_set  = {m for m in history_idx_dic['mame']['machines']} if history_idx_dic else set()
    mameinfo_info_set = {m for m in mameinfo_idx_dic['mame']} if mameinfo_idx_dic else set()

    # --- Built machine plots ---
    pDialog = KodiProgressDialog()
    pDialog.startProgress('Generating MAME machine plots...', len(machines))
    for mname, m in machines.items():
        pDialog.updateProgressInc()
        plot_str_list = mame_MAME_plot_slits(mname, m, assetdb_dic,
            history_info_set, mameinfo_info_set, gameinit_idx_dic, command_idx_dic)
        assetdb_dic[mname]['plot'] = '\n'.join(plot_str_list)
    pDialog.endProgress()

    # Timestamp, save the MAME asset database. Save control_dic at the end.
    db_safe_edit(control_dic, 't_MAME_plots_build', time.time())
    db_files = [
        (assetdb_dic, 'MAME machine assets', cfg.ASSET_DB_PATH.getPath()),
        (control_dic, 'Control dictionary', cfg.MAIN_CONTROL_PATH.getPath()),
    ]
    db_save_files(db_files)

# ---------------------------------------------------------------------------------------------
# Generate plot for Software Lists
# Line 1) SL item has {} parts
# Line 2) {} ROMs and {} disks
# Line 3) Manual, History
# Line 4) Machines: machine list ...
# ---------------------------------------------------------------------------------------------
def mame_build_SL_plots(cfg, SL_dic):
    control_dic = SL_dic['control_dic']
    SL_index_dic = SL_dic['SL_index']
    SL_machines_dic = SL_dic['SL_machines']
    History_idx_dic = SL_dic['history_idx_dic']

    d_text = 'Generating SL item plots ...'
    pDialog = KodiProgressDialog()
    pDialog.startProgress(d_text, len(SL_index_dic))
    for SL_name in sorted(SL_index_dic):
        pDialog.updateProgressInc('{}\nSoftware List {}'.format(d_text, SL_name))

        # Open database
        SL_DB_prefix = SL_index_dic[SL_name]['rom_DB_noext']
        SL_ROMs_FN = cfg.SL_DB_DIR.pjoin(SL_DB_prefix + '_items.json')
        SL_assets_FN = cfg.SL_DB_DIR.pjoin(SL_DB_prefix + '_assets.json')
        SL_ROM_audit_FN = cfg.SL_DB_DIR.pjoin(SL_DB_prefix + '_ROM_audit.json')
        SL_roms = utils_load_JSON_file(SL_ROMs_FN.getPath(), verbose = False)
        SL_assets_dic = utils_load_JSON_file(SL_assets_FN.getPath(), verbose = False)
        SL_ROM_audit_dic = utils_load_JSON_file(SL_ROM_audit_FN.getPath(), verbose = False)
        History_SL_set  = {m for m in History_idx_dic[SL_name]['machines']} if SL_name in History_idx_dic else set()
        # Machine_list = [ m['machine'] for m in SL_machines_dic[SL_name] ]
        # Machines_str = 'Machines: {}'.format(', '.join(sorted(Machine_list)))

        # Traverse SL ROMs and make plot.
        for rom_key in sorted(SL_roms):
            SL_rom = SL_roms[rom_key]
            num_parts = len(SL_rom['parts'])
            if num_parts == 0:   parts_str = 'SL item has no parts'
            elif num_parts == 1: parts_str = 'SL item has {} part'.format(num_parts)
            elif num_parts > 1:  parts_str = 'SL item has {} parts'.format(num_parts)
            num_ROMs = 0
            num_disks = 0
            for SL_rom in SL_ROM_audit_dic[rom_key]:
                if SL_rom['type'] == 'ROM': num_ROMs += 1
                elif SL_rom['type'] == 'DISK': num_disks += 1
            ROM_str = 'ROM' if num_ROMs == 1 else 'ROMs'
            disk_str = 'disk' if num_disks == 1 else 'disks'
            roms_str = '{} {} and {} {}'.format(num_ROMs, ROM_str, num_disks, disk_str)
            Flag_list = []
            if SL_assets_dic[rom_key]['manual']: Flag_list.append('Manual')
            if rom_key in History_SL_set: Flag_list.append('History')
            Flag_str = ', '.join(Flag_list)
            # SL_roms[rom_key]['plot'] = '\n'.join([parts_str, roms_str, Flag_str, Machines_str])
            SL_roms[rom_key]['plot'] = '\n'.join([parts_str, roms_str, Flag_str])
        utils_write_JSON_file(SL_ROMs_FN.getPath(), SL_roms, verbose = False)
    pDialog.endProgress()

    # --- Timestamp ---
    db_safe_edit(control_dic, 't_SL_plots_build', time.time())
    utils_write_JSON_file(cfg.MAIN_CONTROL_PATH.getPath(), control_dic)

# -------------------------------------------------------------------------------------------------
# MAME ROM/CHD audit code
# -------------------------------------------------------------------------------------------------
# This code is very un-optimised! But it is better to get something that works
# and then optimise. "Premature optimization is the root of all evil" -- Donald Knuth
#
# MAME loads ROMs by hash, not by filename. This is the reason MAME is able to load ROMs even
# if they have a wrong name and providing they are in the correct ZIP file (parent or clone set).
#
# Adds new field 'status': ROMS  'OK', 'OK (invalid ROM)', 'ZIP not found', 'Bad ZIP file',
#                                'ROM not in ZIP', 'ROM bad size', 'ROM bad CRC'.
#                          DISKS 'OK', 'OK (invalid CHD)', 'CHD not found', 'CHD bad SHA1'
# Adds fields 'status_colour'.
#
# rom_list = [
#     {'type' : several types, 'name' : 'avph.03d', 'crc' : '01234567', 'location' : 'avsp/avph.03d'}, ...
#     {'type' : 'ROM_TYPE_DISK', 'name' : 'avph.03d', 'sha1' : '012...', 'location' : 'avsp/avph.03d'}, ...
# ]
#
# I'm not sure if the CHD sha1 value in MAME XML is the sha1 of the uncompressed data OR
# the sha1 of the CHD file. If the former, then AML can open the CHD file, get the sha1 from the
# header and verify it. See:
# http://www.mameworld.info/ubbthreads/showflat.php?Cat=&Number=342940&page=0&view=expanded&sb=5&o=&vc=1
#
ZIP_NOT_FOUND = 0
BAD_ZIP_FILE  = 1
ZIP_FILE_OK   = 2
def mame_audit_MAME_machine(cfg, rom_list, audit_dic):
    if cfg.settings['op_mode'] == OP_MODE_VANILLA:
        rom_path = cfg.settings['rom_path_vanilla']
    elif cfg.settings['op_mode'] == OP_MODE_RETRO_MAME2003PLUS:
        rom_path = cfg.settings['rom_path_2003_plus']
    else:
        raise TypeError('Unknown op_mode "{}"'.format(cfg.settings['op_mode']))

    # --- Cache the ROM set ZIP files and detect wrong named files by CRC ---
    # 1) Traverse ROMs, determine the set ZIP files, open ZIP files and put ZIPs in the cache.
    # 2) If a ZIP file is not in the cache is because the ZIP file was not found
    # 3) z_cache_exists is used to check if the ZIP file has been found the first time or not.
    #
    # z_cache = {
    #     'zip_filename' : {
    #         'fname' : {'size' : int, 'crc' : text_type},
    #         'fname' : {'size' : int, 'crc' : text_type}, ...
    #     }
    # }
    #
    # z_cache_status = {
    #      'zip_filename' : ZIP_NOT_FOUND, BAD_ZIP_FILE, ZIP_FILE_OK
    # }
    #
    z_cache = {}
    z_cache_status = {}
    for m_rom in rom_list:
        # Skip CHDs.
        if m_rom['type'] == ROM_TYPE_DISK: continue

        # Process ROM ZIP files.
        set_name = m_rom['location'].split('/')[0]
        if m_rom['type'] == ROM_TYPE_SAMPLE:
            zip_FN = FileName(cfg.settings['samples_path']).pjoin(set_name + '.zip')
        else:
            zip_FN = FileName(rom_path).pjoin(set_name + '.zip')
        zip_path = zip_FN.getPath()

        # ZIP file encountered for the first time. Skip ZIP files already in the cache.
        if zip_path not in z_cache_status:
            if zip_FN.exists():
                # >> Scan files in ZIP file and put them in the cache
                # log_debug('Caching ZIP file {}'.format(zip_path))
                try:
                    zip_f = z.ZipFile(zip_path, 'r')
                except z.BadZipfile as e:
                    z_cache_status[zip_path] = BAD_ZIP_FILE
                    continue
                # log_debug('ZIP {} files {}'.format(m_rom['location'], z_file_list))
                zip_file_dic = {}
                for zfile in zip_f.namelist():
                    # >> NOTE CRC32 in Python is a decimal number: CRC32 4225815809
                    # >> However, MAME encodes it as an hexadecimal number: CRC32 0123abcd
                    z_info = zip_f.getinfo(zfile)
                    z_info_file_size = z_info.file_size
                    z_info_crc_hex_str = '{0:08x}'.format(z_info.CRC)
                    zip_file_dic[zfile] = {'size' : z_info_file_size, 'crc' : z_info_crc_hex_str}
                    # log_debug('ZIP CRC32 {} | CRC hex {} | size {}'.format(z_info.CRC, z_crc_hex, z_info.file_size))
                    # log_debug('ROM CRC hex {} | size {}'.format(m_rom['crc'], 0))
                zip_f.close()
                z_cache[zip_path] = zip_file_dic
                z_cache_status[zip_path] = ZIP_FILE_OK
            else:
                # >> Mark ZIP file as not found
                z_cache_status[zip_path] = ZIP_NOT_FOUND

    # --- Audit ROM by ROM ---
    for m_rom in rom_list:
        if m_rom['type'] == ROM_TYPE_DISK:
            split_list = m_rom['location'].split('/')
            set_name  = split_list[0]
            disk_name = split_list[1]
            # log_debug('Testing CHD {}'.format(m_rom['name']))
            # log_debug('location {}'.format(m_rom['location']))
            # log_debug('set_name  "{}"'.format(set_name))
            # log_debug('disk_name "{}"'.format(disk_name))

            # >> Invalid CHDs
            if not m_rom['sha1']:
                m_rom['status'] = AUDIT_STATUS_OK_INVALID_CHD
                m_rom['status_colour'] = '[COLOR green]{}[/COLOR]'.format(m_rom['status'])
                continue

            # >> Test if DISK file exists
            chd_FN = FileName(cfg.settings['chd_path']).pjoin(set_name).pjoin(disk_name + '.chd')
            # log_debug('chd_FN P {}'.format(chd_FN.getPath()))
            if not chd_FN.exists():
                m_rom['status'] = AUDIT_STATUS_CHD_NO_FOUND
                m_rom['status_colour'] = '[COLOR red]{}[/COLOR]'.format(m_rom['status'])
                continue

            # >> Open CHD file and check SHA1 hash.
            chd_info = _mame_stat_chd(chd_FN.getPath())
            if chd_info['status'] == CHD_BAD_CHD:
                m_rom['status'] = AUDIT_STATUS_BAD_CHD_FILE
                m_rom['status_colour'] = '[COLOR red]{}[/COLOR]'.format(m_rom['status'])
                continue
            if chd_info['status'] == CHD_BAD_VERSION:
                m_rom['status'] = AUDIT_STATUS_CHD_BAD_VERSION
                m_rom['status_colour'] = '[COLOR red]{}[/COLOR]'.format(m_rom['status'])
                continue
            if chd_info['sha1'] != m_rom['sha1']:
                m_rom['status'] = AUDIT_STATUS_CHD_BAD_SHA1
                m_rom['status_colour'] = '[COLOR red]{}[/COLOR]'.format(m_rom['status'])
                continue

            # >> DISK is OK
            m_rom['status'] = AUDIT_STATUS_OK
            m_rom['status_colour'] = '[COLOR green]{}[/COLOR]'.format(m_rom['status'])
        elif m_rom['type'] == ROM_TYPE_SAMPLE:
            split_list = m_rom['location'].split('/')
            set_name = split_list[0]
            sample_name = split_list[1] + '.wav'
            # log_debug('Testing SAMPLE {}'.format(m_rom['name']))
            # log_debug('location       {}'.format(m_rom['location']))
            # log_debug('set_name       {}'.format(set_name))
            # log_debug('sample_name    {}'.format(sample_name))

            # Test if ZIP file exists (use cached data). ZIP file must be in the cache always
            # at this point.
            zip_FN = FileName(cfg.settings['samples_path']).pjoin(set_name + '.zip')
            zip_path = zip_FN.getPath()
            # log_debug('ZIP {}'.format(zip_FN.getPath()))
            if z_cache_status[zip_path] == ZIP_NOT_FOUND:
                m_rom['status'] = AUDIT_STATUS_ZIP_NO_FOUND
                m_rom['status_colour'] = '[COLOR red]{}[/COLOR]'.format(m_rom['status'])
                continue
            elif z_cache_status[zip_path] == BAD_ZIP_FILE:
                m_rom['status'] = AUDIT_STATUS_BAD_ZIP_FILE
                m_rom['status_colour'] = '[COLOR red]{}[/COLOR]'.format(m_rom['status'])
                continue
            # >> ZIP file is good and data was cached.
            zip_file_dic = z_cache[zip_path]

            # >> At this point the ZIP file is in the cache (if it was open)
            if sample_name not in zip_file_dic:
                # >> File not found by filename. Check if it has renamed by looking at CRC.
                # >> ROM not in ZIP (not even under other filename)
                m_rom['status'] = AUDIT_STATUS_SAMPLE_NOT_IN_ZIP
                m_rom['status_colour'] = '[COLOR red]{}[/COLOR]'.format(m_rom['status'])
                continue

            # >> SAMPLE is OK
            m_rom['status'] = AUDIT_STATUS_OK
            m_rom['status_colour'] = '[COLOR green]{}[/COLOR]'.format(m_rom['status'])

        else:
            split_list = m_rom['location'].split('/')
            set_name = split_list[0]
            rom_name = split_list[1]
            # log_debug('Testing ROM {}'.format(m_rom['name']))
            # log_debug('location    {}'.format(m_rom['location']))
            # log_debug('set_name    {}'.format(set_name))
            # log_debug('rom_name    {}'.format(rom_name))

            # >> Invalid ROMs are not in the ZIP file
            if not m_rom['crc']:
                m_rom['status'] = AUDIT_STATUS_OK_INVALID_ROM
                m_rom['status_colour'] = '[COLOR green]{}[/COLOR]'.format(m_rom['status'])
                continue

            # Test if ZIP file exists (use cached data). ZIP file must be in the cache always
            # at this point.
            zip_FN = FileName(rom_path).pjoin(set_name + '.zip')
            zip_path = zip_FN.getPath()
            # log_debug('ZIP {}'.format(zip_FN.getPath()))
            if z_cache_status[zip_path] == ZIP_NOT_FOUND:
                m_rom['status'] = AUDIT_STATUS_ZIP_NO_FOUND
                m_rom['status_colour'] = '[COLOR red]{}[/COLOR]'.format(m_rom['status'])
                continue
            elif z_cache_status[zip_path] == BAD_ZIP_FILE:
                m_rom['status'] = AUDIT_STATUS_BAD_ZIP_FILE
                m_rom['status_colour'] = '[COLOR red]{}[/COLOR]'.format(m_rom['status'])
                continue
            # >> ZIP file is good and data was cached.
            zip_file_dic = z_cache[zip_path]

            # >> At this point the ZIP file is in the cache (if it was open)
            if rom_name in zip_file_dic:
                # >> File has correct name
                if zip_file_dic[rom_name]['size'] != m_rom['size']:
                    m_rom['status'] = AUDIT_STATUS_ROM_BAD_SIZE
                    m_rom['status_colour'] = '[COLOR red]{}[/COLOR]'.format(m_rom['status'])
                    continue
                if zip_file_dic[rom_name]['crc'] != m_rom['crc']:
                    m_rom['status'] = AUDIT_STATUS_ROM_BAD_CRC
                    m_rom['status_colour'] = '[COLOR red]{}[/COLOR]'.format(m_rom['status'])
                    continue
            else:
                # >> File not found by filename. Check if it has renamed by looking at CRC.
                rom_OK_name = ''
                for fn in zip_file_dic:
                    if m_rom['crc'] == zip_file_dic[fn]['crc']:
                        rom_OK_name = fn
                        break
                if rom_OK_name:
                    # >> File found by CRC
                    m_rom['status'] = AUDIT_STATUS_OK_WRONG_NAME_ROM
                    m_rom['status_colour'] = '[COLOR orange]OK (named {})[/COLOR]'.format(rom_OK_name)
                    continue
                else:
                    # >> ROM not in ZIP (not even under other filename)
                    m_rom['status'] = AUDIT_STATUS_ROM_NOT_IN_ZIP
                    m_rom['status_colour'] = '[COLOR red]{}[/COLOR]'.format(m_rom['status'])
                    continue

            # >> ROM is OK
            m_rom['status'] = AUDIT_STATUS_OK
            m_rom['status_colour'] = '[COLOR green]{}[/COLOR]'.format(m_rom['status'])

    # >> Audit results
    # >> Naive and slow code, but better safe than sorry.
    ROM_OK_status_list = []
    SAM_OK_status_list = []
    CHD_OK_status_list = []
    audit_dic['machine_has_ROMs_or_CHDs'] = False
    audit_dic['machine_has_ROMs']         = False
    audit_dic['machine_has_SAMPLES']      = False
    audit_dic['machine_has_CHDs']         = False
    for m_rom in rom_list:
        audit_dic['machine_has_ROMs_or_CHDs'] = True
        if m_rom['type'] == ROM_TYPE_DISK:
            audit_dic['machine_has_CHDs'] = True
            if m_rom['status'] == AUDIT_STATUS_OK or m_rom['status'] == AUDIT_STATUS_OK_INVALID_CHD:
                CHD_OK_status_list.append(True)
            else:
                CHD_OK_status_list.append(False)
        elif m_rom['type'] == ROM_TYPE_SAMPLE:
            audit_dic['machine_has_SAMPLES'] = True
            if m_rom['status'] == AUDIT_STATUS_OK:
                SAM_OK_status_list.append(True)
            else:
                SAM_OK_status_list.append(False)
        else:
            audit_dic['machine_has_ROMs'] = True
            if m_rom['status'] == AUDIT_STATUS_OK or \
                m_rom['status'] == AUDIT_STATUS_OK_INVALID_ROM or \
                m_rom['status'] == AUDIT_STATUS_OK_WRONG_NAME_ROM:
                ROM_OK_status_list.append(True)
            else:
                ROM_OK_status_list.append(False)
    audit_dic['machine_ROMs_are_OK']    = all(ROM_OK_status_list) if audit_dic['machine_has_ROMs'] else True
    audit_dic['machine_SAMPLES_are_OK'] = all(SAM_OK_status_list) if audit_dic['machine_has_SAMPLES'] else True
    audit_dic['machine_CHDs_are_OK']    = all(CHD_OK_status_list) if audit_dic['machine_has_CHDs'] else True
    audit_dic['machine_is_OK'] = audit_dic['machine_ROMs_are_OK'] and \
        audit_dic['machine_SAMPLES_are_OK'] and audit_dic['machine_CHDs_are_OK']

# -------------------------------------------------------------------------------------------------
# SL ROM/CHD audit code
# -------------------------------------------------------------------------------------------------
def mame_audit_SL_machine(SL_ROM_path_FN, SL_CHD_path_FN, SL_name, item_name, rom_list, audit_dic):
    # --- Cache the ROM set ZIP files and detect wrong named files by CRC ---
    # >> Look at mame_audit_MAME_machine() for comments.
    z_cache = {}
    z_cache_status = {}
    for m_rom in rom_list:
        # >> Skip CHDs
        if m_rom['type'] == ROM_TYPE_DISK: continue

        # >> Process ROM ZIP files
        split_list = m_rom['location'].split('/')
        SL_name  = split_list[0]
        zip_name = split_list[1] + '.zip'
        zip_FN = SL_ROM_path_FN.pjoin(SL_name).pjoin(zip_name)
        zip_path = zip_FN.getPath()

        # >> ZIP file encountered for the first time. Skip ZIP files already in the cache.
        if zip_path not in z_cache_status:
            if zip_FN.exists():
                # >> Scan files in ZIP file and put them in the cache
                # log_debug('Caching ZIP file {}'.format(zip_path))
                try:
                    zip_f = z.ZipFile(zip_path, 'r')
                except z.BadZipfile as e:
                    z_cache_status[zip_path] = BAD_ZIP_FILE
                    continue
                # log_debug('ZIP {} files {}'.format(m_rom['location'], z_file_list))
                zip_file_dic = {}
                for zfile in zip_f.namelist():
                    # >> NOTE CRC32 in Python is a decimal number: CRC32 4225815809
                    # >> However, MAME encodes it as an hexadecimal number: CRC32 0123abcd
                    z_info = zip_f.getinfo(zfile)
                    z_info_file_size = z_info.file_size
                    z_info_crc_hex_str = '{0:08x}'.format(z_info.CRC)
                    # Unicode filenames in ZIP files cause problems later in this function.
                    # zfile has type Unicode and it's not encoded in utf-8.
                    # How to know encoding of ZIP files?
                    # https://stackoverflow.com/questions/15918314/how-to-detect-string-byte-encoding/15918519
                    try:
                        # zfile sometimes has type Unicode, sometimes str. If type is str then
                        # try to decode it as UTF-8.
                        if type(zfile) == text_type:
                            zfile_unicode = zfile
                        else:
                            zfile_unicode = zfile.decode('utf-8')
                    except UnicodeDecodeError:
                        log_error('mame_audit_SL_machine() Exception UnicodeDecodeError')
                        log_error('type(zfile) = {}'.format(type(zfile)))
                        log_error('SL_name "{}", item_name "{}", rom name "{}"'.format(SL_name, item_name, m_rom['name']))
                    except UnicodeEncodeError:
                        log_error('mame_audit_SL_machine() Exception UnicodeEncodeError')
                        log_error('type(zfile) = {}'.format(type(zfile)))
                        log_error('SL_name "{}", item_name "{}", rom name "{}"'.format(SL_name, item_name, m_rom['name']))
                    else:
                        # For now, do not add non-ASCII ROMs so the audit will fail for this ROM.
                        zip_file_dic[zfile_unicode] = {'size' : z_info_file_size, 'crc' : z_info_crc_hex_str}
                    # log_debug('ZIP CRC32 {} | CRC hex {} | size {}'.format(z_info.CRC, z_crc_hex, z_info.file_size))
                    # log_debug('ROM CRC hex {} | size {}'.format(m_rom['crc'], 0))
                zip_f.close()
                z_cache[zip_path] = zip_file_dic
                z_cache_status[zip_path] = ZIP_FILE_OK
            else:
                # >> Mark ZIP file as not found
                z_cache_status[zip_path] = ZIP_NOT_FOUND

    # --- Audit ROM by ROM ---
    for m_rom in rom_list:
        if m_rom['type'] == ROM_TYPE_DISK:
            # --- Audit CHD ----------------------------------------------------------------------
            split_list = m_rom['location'].split('/')
            SL_name   = split_list[0]
            item_name = split_list[1]
            disk_name = split_list[2]
            # log_debug('Testing CHD "{}"'.format(m_rom['name']))
            # log_debug('location "{}"'.format(m_rom['location']))
            # log_debug('SL_name   "{}"'.format(SL_name))
            # log_debug('item_name "{}"'.format(item_name))
            # log_debug('disk_name "{}"'.format(disk_name))

            # >> Invalid CHDs
            if not m_rom['sha1']:
                m_rom['status'] = AUDIT_STATUS_OK_INVALID_CHD
                m_rom['status_colour'] = '[COLOR green]{}[/COLOR]'.format(m_rom['status'])
                continue

            # >> Test if DISK file exists
            chd_FN = SL_CHD_path_FN.pjoin(SL_name).pjoin(item_name).pjoin(disk_name + '.chd')
            # log_debug('chd_FN P {}'.format(chd_FN.getPath()))
            if not chd_FN.exists():
                m_rom['status'] = AUDIT_STATUS_CHD_NO_FOUND
                m_rom['status_colour'] = '[COLOR red]{}[/COLOR]'.format(m_rom['status'])
                continue

            # >> Open CHD file and check SHA1 hash.
            chd_info = _mame_stat_chd(chd_FN.getPath())
            if chd_info['status'] == CHD_BAD_CHD:
                m_rom['status'] = AUDIT_STATUS_BAD_CHD_FILE
                m_rom['status_colour'] = '[COLOR red]{}[/COLOR]'.format(m_rom['status'])
                continue
            if chd_info['status'] == CHD_BAD_VERSION:
                m_rom['status'] = AUDIT_STATUS_CHD_BAD_VERSION
                m_rom['status_colour'] = '[COLOR red]{}[/COLOR]'.format(m_rom['status'])
                continue
            if chd_info['sha1'] != m_rom['sha1']:
                m_rom['status'] = AUDIT_STATUS_CHD_BAD_SHA1
                m_rom['status_colour'] = '[COLOR red]{}[/COLOR]'.format(m_rom['status'])
                continue

            # >> DISK is OK
            m_rom['status'] = AUDIT_STATUS_OK
            m_rom['status_colour'] = '[COLOR green]{}[/COLOR]'.format(m_rom['status'])
        else:
            # --- Audit ROM ----------------------------------------------------------------------
            split_list = m_rom['location'].split('/')
            SL_name   = split_list[0]
            item_name = split_list[1]
            rom_name  = split_list[2]
            # log_debug('Testing ROM "{}"'.format(m_rom['name']))
            # log_debug('location "{}"'.format(m_rom['location']))
            # log_debug('SL_name   "{}"'.format(SL_name))
            # log_debug('item_name "{}"'.format(item_name))
            # log_debug('rom_name  "{}"'.format(rom_name))

            # >> Invalid ROMs are not in the ZIP file
            if not m_rom['crc']:
                m_rom['status'] = AUDIT_STATUS_OK_INVALID_ROM
                m_rom['status_colour'] = '[COLOR green]{}[/COLOR]'.format(m_rom['status'])
                continue

            # >> Test if ZIP file exists
            zip_FN = SL_ROM_path_FN.pjoin(SL_name).pjoin(item_name + '.zip')
            zip_path = zip_FN.getPath()
            # log_debug('zip_FN P {}'.format(zip_FN.getPath()))
            if z_cache_status[zip_path] == ZIP_NOT_FOUND:
                m_rom['status'] = AUDIT_STATUS_ZIP_NO_FOUND
                m_rom['status_colour'] = '[COLOR red]{}[/COLOR]'.format(m_rom['status'])
                continue
            elif z_cache_status[zip_path] == BAD_ZIP_FILE:
                m_rom['status'] = AUDIT_STATUS_BAD_ZIP_FILE
                m_rom['status_colour'] = '[COLOR red]{}[/COLOR]'.format(m_rom['status'])
                continue
            # >> ZIP file is good and data was cached.
            zip_file_dic = z_cache[zip_path]

            # >> At this point the ZIP file is in the cache (if it was open)
            if rom_name in zip_file_dic:
                # >> File has correct name
                if zip_file_dic[rom_name]['size'] != m_rom['size']:
                    m_rom['status'] = AUDIT_STATUS_ROM_BAD_SIZE
                    m_rom['status_colour'] = '[COLOR red]{}[/COLOR]'.format(m_rom['status'])
                    continue
                if zip_file_dic[rom_name]['crc'] != m_rom['crc']:
                    m_rom['status'] = AUDIT_STATUS_ROM_BAD_CRC
                    m_rom['status_colour'] = '[COLOR red]{}[/COLOR]'.format(m_rom['status'])
                    continue
            else:
                # >> File not found by filename. Check if it has renamed by looking at CRC.
                rom_OK_name = ''
                for fn in zip_file_dic:
                    if m_rom['crc'] == zip_file_dic[fn]['crc']:
                        rom_OK_name = fn
                        break
                if rom_OK_name:
                    # >> File found by CRC
                    m_rom['status'] = AUDIT_STATUS_OK_WRONG_NAME_ROM
                    m_rom['status_colour'] = '[COLOR orange]OK (named {})[/COLOR]'.format(rom_OK_name)
                    continue
                else:
                    # >> ROM not in ZIP (not even under other filename)
                    m_rom['status'] = AUDIT_STATUS_ROM_NOT_IN_ZIP
                    m_rom['status_colour'] = '[COLOR red]{}[/COLOR]'.format(m_rom['status'])
                    continue

            # >> ROM is OK
            m_rom['status'] = AUDIT_STATUS_OK
            m_rom['status_colour'] = '[COLOR green]{}[/COLOR]'.format(m_rom['status'])
            # log_debug('{}'.format(AUDIT_STATUS_OK))

    # >> Currently exactly same code as in mame_audit_MAME_machine()
    # >> Audit results
    # >> Naive and slow code, but better safe than sorry.
    ROM_OK_status_list = []
    CHD_OK_status_list = []
    audit_dic['machine_has_ROMs_or_CHDs'] = False
    audit_dic['machine_has_ROMs']         = False
    audit_dic['machine_has_CHDs']         = False
    for m_rom in rom_list:
        audit_dic['machine_has_ROMs_or_CHDs'] = True
        if m_rom['type'] == ROM_TYPE_DISK:
            audit_dic['machine_has_CHDs'] = True
            if m_rom['status'] == AUDIT_STATUS_OK or \
               m_rom['status'] == AUDIT_STATUS_OK_INVALID_CHD:
                CHD_OK_status_list.append(True)
            else:
                CHD_OK_status_list.append(False)
        else:
            audit_dic['machine_has_ROMs'] = True
            if m_rom['status'] == AUDIT_STATUS_OK or \
               m_rom['status'] == AUDIT_STATUS_OK_INVALID_ROM or \
               m_rom['status'] == AUDIT_STATUS_OK_WRONG_NAME_ROM:
                ROM_OK_status_list.append(True)
            else:
                ROM_OK_status_list.append(False)
    audit_dic['machine_ROMs_are_OK'] = all(ROM_OK_status_list) if audit_dic['machine_has_ROMs'] else True
    audit_dic['machine_CHDs_are_OK'] = all(CHD_OK_status_list) if audit_dic['machine_has_CHDs'] else True
    audit_dic['machine_is_OK'] = audit_dic['machine_ROMs_are_OK'] and audit_dic['machine_CHDs_are_OK']

def mame_audit_MAME_all(cfg, db_dic_in):
    log_debug('mame_audit_MAME_all() Initialising...')
    control_dic = db_dic_in['control_dic']
    machines = db_dic_in['machines']
    renderdb_dic = db_dic_in['renderdb']
    audit_roms_dic = db_dic_in['audit_roms']

    # Go machine by machine and audit ZIPs and CHDs. Adds new column 'status' to each ROM.
    pDialog = KodiProgressDialog()
    pDialog.startProgress('Auditing MAME ROMs and CHDs...', len(renderdb_dic))
    machine_audit_dic = {}
    for m_name in sorted(renderdb_dic):
        pDialog.updateProgressInc()
        if pDialog.isCanceled(): break
        # Only audit machine if it has ROMs. However, add all machines to machine_audit_dic.
        # audit_roms_dic[m_name] is mutable and edited inside mame_audit_MAME_machine()
        audit_dic = db_new_audit_dic()
        if m_name in audit_roms_dic:
            mame_audit_MAME_machine(cfg, audit_roms_dic[m_name], audit_dic)
        machine_audit_dic[m_name] = audit_dic
    pDialog.endProgress()

    # Audit statistics.
    audit_MAME_machines_with_arch        = 0
    audit_MAME_machines_with_arch_OK     = 0
    audit_MAME_machines_with_arch_BAD    = 0
    audit_MAME_machines_without          = 0
    audit_MAME_machines_with_ROMs        = 0
    audit_MAME_machines_with_ROMs_OK     = 0
    audit_MAME_machines_with_ROMs_BAD    = 0
    audit_MAME_machines_without_ROMs     = 0
    audit_MAME_machines_with_SAMPLES     = 0
    audit_MAME_machines_with_SAMPLES_OK  = 0
    audit_MAME_machines_with_SAMPLES_BAD = 0
    audit_MAME_machines_without_SAMPLES  = 0
    audit_MAME_machines_with_CHDs        = 0
    audit_MAME_machines_with_CHDs_OK     = 0
    audit_MAME_machines_with_CHDs_BAD    = 0
    audit_MAME_machines_without_CHDs     = 0
    for m_name in renderdb_dic:
        render_dic = renderdb_dic[m_name]
        audit_dic = machine_audit_dic[m_name]
        # Skip unrunnable (device) machines
        if render_dic['isDevice']: continue
        if audit_dic['machine_has_ROMs_or_CHDs']:
            audit_MAME_machines_with_arch += 1
            if audit_dic['machine_is_OK']: audit_MAME_machines_with_arch_OK += 1
            else:                          audit_MAME_machines_with_arch_BAD += 1
        else:
            audit_MAME_machines_without += 1

        if audit_dic['machine_has_ROMs']:
            audit_MAME_machines_with_ROMs += 1
            if audit_dic['machine_ROMs_are_OK']: audit_MAME_machines_with_ROMs_OK += 1
            else:                                audit_MAME_machines_with_ROMs_BAD += 1
        else:
            audit_MAME_machines_without_ROMs += 1

        if audit_dic['machine_has_SAMPLES']:
            audit_MAME_machines_with_SAMPLES += 1
            if audit_dic['machine_SAMPLES_are_OK']: audit_MAME_machines_with_SAMPLES_OK += 1
            else:                                   audit_MAME_machines_with_SAMPLES_BAD += 1
        else:
            audit_MAME_machines_without_SAMPLES += 1

        if audit_dic['machine_has_CHDs']:
            audit_MAME_machines_with_CHDs += 1
            if audit_dic['machine_CHDs_are_OK']: audit_MAME_machines_with_CHDs_OK += 1
            else:                                audit_MAME_machines_with_CHDs_BAD += 1
        else:
            audit_MAME_machines_without_CHDs += 1

    # --- Report header and statistics ---
    report_full_list = [
        '*** Advanced MAME Launcher MAME audit report ***',
        'This report shows full audit report',
    ]
    report_good_list = [
        '*** Advanced MAME Launcher MAME audit report ***',
        'This report shows machines with good ROMs and/or CHDs',
    ]
    report_error_list = [
        '*** Advanced MAME Launcher MAME audit report ***',
        'This report shows machines with bad/missing ROMs and/or CHDs',
    ]
    ROM_report_good_list = [
        '*** Advanced MAME Launcher MAME audit report ***',
        'This report shows machines with good ROMs',
    ]
    ROM_report_error_list = [
        '*** Advanced MAME Launcher MAME audit report ***',
        'This report shows machines with bad/missing ROMs',
    ]
    SAMPLES_report_good_list = [
        '*** Advanced MAME Launcher MAME audit report ***',
        'This report shows machines with good Samples',
    ]
    SAMPLES_report_error_list = [
        '*** Advanced MAME Launcher MAME audit report ***',
        'This report shows machines with bad/missing Samples',
    ]
    CHD_report_good_list = [
        '*** Advanced MAME Launcher MAME audit report ***',
        'This report shows machines with good CHDs',
    ]
    CHD_report_error_list = [
        '*** Advanced MAME Launcher MAME audit report ***',
        'This report shows machines with bad/missing CHDs',
    ]
    h_list = [
        'There are {} machines in total'.format(len(renderdb_dic)),
        'Of those, {} are runnable machines'.format(control_dic['stats_audit_MAME_machines_runnable']),
    ]
    report_full_list.extend(h_list)
    report_good_list.extend(h_list)
    report_error_list.extend(h_list)
    ROM_report_good_list.extend(h_list)
    ROM_report_error_list.extend(h_list)
    SAMPLES_report_good_list.extend(h_list)
    SAMPLES_report_error_list.extend(h_list)
    CHD_report_good_list.extend(h_list)
    CHD_report_error_list.extend(h_list)

    h_list = [
        'Of those, {} require ROMs and or CHDSs'.format(audit_MAME_machines_with_arch),
        'Of those, {} are OK and {} have bad/missing ROMs and/or CHDs'.format(
            audit_MAME_machines_with_arch_OK, audit_MAME_machines_with_arch_BAD ),
    ]
    report_good_list.extend(h_list)
    report_error_list.extend(h_list)
    h_list = [
        'Of those, {} require ROMs'.format(audit_MAME_machines_with_ROMs),
        'Of those, {} are OK and {} have bad/missing ROMs and/or CHDs'.format(
            audit_MAME_machines_with_ROMs_OK, audit_MAME_machines_with_ROMs_BAD ),
    ]
    ROM_report_good_list.extend(h_list)
    ROM_report_error_list.extend(h_list)
    h_list = [
        'Of those, {} require ROMs and or CHDSs'.format(audit_MAME_machines_with_CHDs),
        'Of those, {} are OK and {} have bad/missing ROMs and/or CHDs'.format(
            audit_MAME_machines_with_CHDs_OK, audit_MAME_machines_with_CHDs_BAD ),
    ]
    CHD_report_good_list.extend(h_list)
    CHD_report_error_list.extend(h_list)

    report_full_list.append('')
    report_good_list.append('')
    report_error_list.append('')
    ROM_report_good_list.append('')
    ROM_report_error_list.append('')
    SAMPLES_report_good_list.append('')
    SAMPLES_report_error_list.append('')
    CHD_report_good_list.append('')
    CHD_report_error_list.append('')

    # Generate report.
    pDialog.startProgress('Generating audit reports...', len(renderdb_dic))
    for m_name in sorted(renderdb_dic):
        pDialog.updateProgressInc()

        # Skip ROMless and/or CHDless machines from reports, except the full report
        description = renderdb_dic[m_name]['description']
        cloneof = renderdb_dic[m_name]['cloneof']
        if m_name not in audit_roms_dic:
            head_list = []
            head_list.append('Machine {} "{}"'.format(m_name, description))
            if cloneof:
                clone_desc = renderdb_dic[cloneof]['description']
                head_list.append('Cloneof {} "{}"'.format(cloneof, clone_desc))
            head_list.append('This machine has no ROMs and/or CHDs')
            report_full_list.extend(head_list)
            continue
        rom_list = audit_roms_dic[m_name]
        if not rom_list: continue

        # >> Check if audit was canceled.
        # log_debug(text_type(rom_list))
        if 'status' not in rom_list[0]:
            report_list.append('Audit was canceled at machine {}'.format(m_name))
            break

        # >> Machine header (in all reports).
        head_list = []
        head_list.append('Machine {} "{}"'.format(m_name, description))
        if cloneof:
            clone_desc = renderdb_dic[cloneof]['description']
            head_list.append('Cloneof {} "{}"'.format(cloneof, clone_desc))

        # ROM/CHD report.
        table_str = [ ['right', 'left', 'right', 'left', 'left', 'left'] ]
        for m_rom in rom_list:
            if m_rom['type'] == ROM_TYPE_DISK:
                table_row = [m_rom['type'], m_rom['name'], '', m_rom['sha1'][0:8],
                    m_rom['location'], m_rom['status']]
            elif m_rom['type'] == ROM_TYPE_SAMPLE:
                table_row = [m_rom['type'], m_rom['name'], '', '', m_rom['location'], m_rom['status']]
            else:
                table_row = [m_rom['type'], m_rom['name'], text_type(m_rom['size']), m_rom['crc'],
                    m_rom['location'], m_rom['status']]
            table_str.append(table_row)
        local_str_list = text_render_table_NO_HEADER(table_str)
        local_str_list.append('')

        # --- At this point all machines have ROMs and/or CHDs ---
        # >> Full, ROMs and/or CHDs report.
        audit_dic = machine_audit_dic[m_name]
        report_full_list.extend(head_list + local_str_list)
        if audit_dic['machine_is_OK']:
            report_good_list.extend(head_list + local_str_list)
        else:
            report_error_list.extend(head_list + local_str_list)

        # >> ROM report
        if audit_dic['machine_has_ROMs']:
            if audit_dic['machine_ROMs_are_OK']:
                ROM_report_good_list.extend(head_list + local_str_list)
            else:
                ROM_report_error_list.extend(head_list + local_str_list)

        # >> Samples report
        if audit_dic['machine_has_SAMPLES']:
            if audit_dic['machine_SAMPLES_are_OK']:
                SAMPLES_report_good_list.extend(head_list + local_str_list)
            else:
                SAMPLES_report_error_list.extend(head_list + local_str_list)

        # >> CHD report.
        if audit_dic['machine_has_CHDs']:
            if audit_dic['machine_CHDs_are_OK']:
                CHD_report_good_list.extend(head_list + local_str_list)
            else:
                CHD_report_error_list.extend(head_list + local_str_list)
    else:
        a = '*** MAME audit finished ***'
        report_full_list.append(a)
        report_good_list.append(a)
        report_error_list.append(a)
        ROM_report_good_list.append(a)
        ROM_report_error_list.append(a)
        SAMPLES_report_good_list.append(a)
        SAMPLES_report_error_list.append(a)
        CHD_report_good_list.append(a)
        CHD_report_error_list.append(a)
    pDialog.endProgress()

    # --- Write reports ---
    num_items = 9
    pDialog.startProgress('Writing report files...', num_items)
    utils_write_slist_to_file(cfg.REPORT_MAME_AUDIT_FULL_PATH.getPath(), report_full_list)
    pDialog.updateProgress(1)
    utils_write_slist_to_file(cfg.REPORT_MAME_AUDIT_GOOD_PATH.getPath(), report_good_list)
    pDialog.updateProgress(2)
    utils_write_slist_to_file(cfg.REPORT_MAME_AUDIT_ERRORS_PATH.getPath(), report_error_list)
    pDialog.updateProgress(3)
    utils_write_slist_to_file(cfg.REPORT_MAME_AUDIT_ROM_GOOD_PATH.getPath(), ROM_report_good_list)
    pDialog.updateProgress(4)
    utils_write_slist_to_file(cfg.REPORT_MAME_AUDIT_ROM_ERRORS_PATH.getPath(), ROM_report_error_list)
    pDialog.updateProgress(5)
    utils_write_slist_to_file(cfg.REPORT_MAME_AUDIT_SAMPLES_GOOD_PATH.getPath(), SAMPLES_report_good_list)
    pDialog.updateProgress(6)
    utils_write_slist_to_file(cfg.REPORT_MAME_AUDIT_SAMPLES_ERRORS_PATH.getPath(), SAMPLES_report_error_list)
    pDialog.updateProgress(7)
    utils_write_slist_to_file(cfg.REPORT_MAME_AUDIT_CHD_GOOD_PATH.getPath(), CHD_report_good_list)
    pDialog.updateProgress(8)
    utils_write_slist_to_file(cfg.REPORT_MAME_AUDIT_CHD_ERRORS_PATH.getPath(), CHD_report_error_list)
    pDialog.endProgress()

    # Update MAME audit statistics.
    db_safe_edit(control_dic, 'audit_MAME_machines_with_arch', audit_MAME_machines_with_arch)
    db_safe_edit(control_dic, 'audit_MAME_machines_with_arch_OK', audit_MAME_machines_with_arch_OK)
    db_safe_edit(control_dic, 'audit_MAME_machines_with_arch_BAD', audit_MAME_machines_with_arch_BAD)
    db_safe_edit(control_dic, 'audit_MAME_machines_without', audit_MAME_machines_without)
    db_safe_edit(control_dic, 'audit_MAME_machines_with_ROMs', audit_MAME_machines_with_ROMs)
    db_safe_edit(control_dic, 'audit_MAME_machines_with_ROMs_OK', audit_MAME_machines_with_ROMs_OK)
    db_safe_edit(control_dic, 'audit_MAME_machines_with_ROMs_BAD', audit_MAME_machines_with_ROMs_BAD)
    db_safe_edit(control_dic, 'audit_MAME_machines_without_ROMs', audit_MAME_machines_without_ROMs)
    db_safe_edit(control_dic, 'audit_MAME_machines_with_SAMPLES', audit_MAME_machines_with_SAMPLES)
    db_safe_edit(control_dic, 'audit_MAME_machines_with_SAMPLES_OK', audit_MAME_machines_with_SAMPLES_OK)
    db_safe_edit(control_dic, 'audit_MAME_machines_with_SAMPLES_BAD', audit_MAME_machines_with_SAMPLES_BAD)
    db_safe_edit(control_dic, 'audit_MAME_machines_without_SAMPLES', audit_MAME_machines_without_SAMPLES)
    db_safe_edit(control_dic, 'audit_MAME_machines_with_CHDs', audit_MAME_machines_with_CHDs)
    db_safe_edit(control_dic, 'audit_MAME_machines_with_CHDs_OK', audit_MAME_machines_with_CHDs_OK)
    db_safe_edit(control_dic, 'audit_MAME_machines_with_CHDs_BAD', audit_MAME_machines_with_CHDs_BAD)
    db_safe_edit(control_dic, 'audit_MAME_machines_without_CHDs', audit_MAME_machines_without_CHDs)

    # Update timestamp of ROM audit.
    db_safe_edit(control_dic, 't_MAME_audit', time.time())
    utils_write_JSON_file(cfg.MAIN_CONTROL_PATH.getPath(), control_dic)

def mame_audit_SL_all(cfg, db_dic_in):
    log_debug('mame_audit_SL_all() Initialising ...')
    control_dic = db_dic_in['control_dic']
    SL_index_dic = db_dic_in['SL_index']

    # Report header and statistics
    report_full_list = [
        '*** Advanced MAME Launcher Software Lists audit report ***',
        'This report shows full Software Lists audit report',
    ]
    report_good_list = [
        '*** Advanced MAME Launcher Software Lists audit report ***',
        'This report shows SL items with good ROMs and/or CHDs',
    ]
    report_error_list = [
        '*** Advanced MAME Launcher Software Lists audit report ***',
        'This report shows SL items with errors in ROMs and/or CHDs',
    ]
    ROM_report_good_list = [
        '*** Advanced MAME Launcher Software Lists audit report ***',
        'This report shows SL items with good ROMs',
    ]
    ROM_report_error_list = [
        '*** Advanced MAME Launcher Software Lists audit report ***',
        'This report shows SL items with errors in ROMs',
    ]
    CHD_report_good_list  = [
        '*** Advanced MAME Launcher Software Lists audit report ***',
        'This report shows SL items with good CHDs',
    ]
    CHD_report_error_list = [
        '*** Advanced MAME Launcher Software Lists audit report ***',
        'This report shows SL items with errors in CHDs',
    ]
    h_list = [
        'There are {} software lists'.format(len(SL_index_dic)),
        '',
    ]
    report_full_list.extend(h_list)
    report_good_list.extend(h_list)
    report_error_list.extend(h_list)
    ROM_report_good_list.extend(h_list)
    ROM_report_error_list.extend(h_list)
    CHD_report_good_list.extend(h_list)
    CHD_report_error_list.extend(h_list)

    # DEBUG code
    # SL_index_dic = {
    #     "32x" : {
    #         "display_name" : "Sega 32X cartridges",
    #         "num_with_CHDs" : 0,
    #         "num_with_ROMs" : 203,
    #         "rom_DB_noext" : "32x"
    #     }
    # }

    # SL audit statistics.
    audit_SL_items_runnable          = 0
    audit_SL_items_with_arch         = 0
    audit_SL_items_with_arch_OK      = 0
    audit_SL_items_with_arch_BAD     = 0
    audit_SL_items_without_arch      = 0
    audit_SL_items_with_arch_ROM     = 0
    audit_SL_items_with_arch_ROM_OK  = 0
    audit_SL_items_with_arch_ROM_BAD = 0
    audit_SL_items_without_arch_ROM  = 0
    audit_SL_items_with_CHD          = 0
    audit_SL_items_with_CHD_OK       = 0
    audit_SL_items_with_CHD_BAD      = 0
    audit_SL_items_without_CHD       = 0

    # Iterate all SL databases and audit ROMs.
    d_text = 'Auditing Sofware Lists ROMs and CHDs...'
    pDialog = KodiProgressDialog()
    pDialog.startProgress(d_text, len(SL_index_dic))
    SL_ROM_path_FN = FileName(cfg.settings['SL_rom_path'])
    SL_CHD_path_FN = FileName(cfg.settings['SL_chd_path'])
    for SL_name in sorted(SL_index_dic):
        pDialog.updateProgressInc('{}\nSoftware List {}'.format(d_text, SL_name))

        SL_dic = SL_index_dic[SL_name]
        SL_DB_FN = cfg.SL_DB_DIR.pjoin(SL_dic['rom_DB_noext'] + '_items.json')
        SL_AUDIT_ROMs_DB_FN = cfg.SL_DB_DIR.pjoin(SL_dic['rom_DB_noext'] + '_ROM_audit.json')
        roms = utils_load_JSON_file(SL_DB_FN.getPath(), verbose = False)
        audit_roms = utils_load_JSON_file(SL_AUDIT_ROMs_DB_FN.getPath(), verbose = False)

        # Iterate SL ROMs
        for rom_key in sorted(roms):
            # audit_roms_list and audit_dic are mutable and edited inside the function()
            audit_rom_list = audit_roms[rom_key]
            audit_dic = db_new_audit_dic()
            mame_audit_SL_machine(SL_ROM_path_FN, SL_CHD_path_FN, SL_name, rom_key, audit_rom_list, audit_dic)

            # Audit statistics
            audit_SL_items_runnable += 1
            if audit_dic['machine_has_ROMs_or_CHDs']:
                audit_SL_items_with_arch += 1
                if audit_dic['machine_is_OK']: audit_SL_items_with_arch_OK += 1
                else:                          audit_SL_items_with_arch_BAD += 1
            else:
                audit_SL_items_without_arch += 1

            if audit_dic['machine_has_ROMs']:
                audit_SL_items_with_arch_ROM += 1
                if audit_dic['machine_ROMs_are_OK']: audit_SL_items_with_arch_ROM_OK += 1
                else:                                audit_SL_items_with_arch_ROM_BAD += 1
            else:
                audit_SL_items_without_arch_ROM += 1

            if audit_dic['machine_has_CHDs']:
                audit_SL_items_with_CHD += 1
                if audit_dic['machine_CHDs_are_OK']: audit_SL_items_with_CHD_OK += 1
                else:                                audit_SL_items_with_CHD_BAD += 1
            else:
                audit_SL_items_without_CHD += 1

            # Software/machine header.
            # WARNING: Kodi crashes with a 22 MB text file with colours. No problem if TXT file has not colours.
            rom = roms[rom_key]
            cloneof = rom['cloneof']
            head_list = []
            if cloneof:
                head_list.append('SL {} ROM {} (cloneof {})'.format(SL_name, rom_key, cloneof))
            else:
                head_list.append('SL {} ROM {}'.format(SL_name, rom_key))

            # ROM/CHD report.
            table_str = [ ['right', 'left', 'left', 'left', 'left'] ]
            for m_rom in audit_rom_list:
                if m_rom['type'] == ROM_TYPE_DISK:
                    table_row = [m_rom['type'], '',
                                 m_rom['sha1'][0:8], m_rom['location'], m_rom['status']]
                else:
                    table_row = [m_rom['type'], text_type(m_rom['size']),
                                 m_rom['crc'], m_rom['location'], m_rom['status']]
                table_str.append(table_row)
            local_str_list = text_render_table_NO_HEADER(table_str)
            local_str_list.append('')

            # Full, ROMs and CHDs report.
            report_full_list.extend(head_list + local_str_list)
            if audit_dic['machine_is_OK']:
                report_good_list.extend(head_list + local_str_list)
            else:
                report_error_list.extend(head_list + local_str_list)

            # ROM report
            if audit_dic['machine_has_ROMs']:
                if audit_dic['machine_ROMs_are_OK']:
                    ROM_report_good_list.extend(head_list + local_str_list)
                else:
                    ROM_report_error_list.extend(head_list + local_str_list)

            # CHD report.
            if audit_dic['machine_has_CHDs']:
                if audit_dic['machine_CHDs_are_OK']:
                    CHD_report_good_list.extend(head_list + local_str_list)
                else:
                    CHD_report_error_list.extend(head_list + local_str_list)
    a = '*** Software Lists audit finished ***'
    report_full_list.append(a)
    report_good_list.append(a)
    report_error_list.append(a)
    ROM_report_good_list.append(a)
    ROM_report_error_list.append(a)
    CHD_report_good_list.append(a)
    CHD_report_error_list.append(a)
    pDialog.endProgress()

    # Write reports.
    num_items = 7
    pDialog.startProgress('Writing SL audit reports...', num_items)
    utils_write_slist_to_file(cfg.REPORT_SL_AUDIT_FULL_PATH.getPath(), report_full_list)
    pDialog.updateProgress(1)
    utils_write_slist_to_file(cfg.REPORT_SL_AUDIT_GOOD_PATH.getPath(), report_good_list)
    pDialog.updateProgress(2)
    utils_write_slist_to_file(cfg.REPORT_SL_AUDIT_ERRORS_PATH.getPath(), report_error_list)
    pDialog.updateProgress(3)
    utils_write_slist_to_file(cfg.REPORT_SL_AUDIT_ROMS_GOOD_PATH.getPath(), ROM_report_good_list)
    pDialog.updateProgress(4)
    utils_write_slist_to_file(cfg.REPORT_SL_AUDIT_ROMS_ERRORS_PATH.getPath(), ROM_report_error_list)
    pDialog.updateProgress(5)
    utils_write_slist_to_file(cfg.REPORT_SL_AUDIT_CHDS_GOOD_PATH.getPath(), CHD_report_good_list)
    pDialog.updateProgress(6)
    utils_write_slist_to_file(cfg.REPORT_SL_AUDIT_CHDS_ERRORS_PATH.getPath(), CHD_report_error_list)
    pDialog.endProgress()

    # Update SL audit statistics.
    db_safe_edit(control_dic, 'audit_SL_items_runnable', audit_SL_items_runnable)
    db_safe_edit(control_dic, 'audit_SL_items_with_arch', audit_SL_items_with_arch)
    db_safe_edit(control_dic, 'audit_SL_items_with_arch_OK', audit_SL_items_with_arch_OK)
    db_safe_edit(control_dic, 'audit_SL_items_with_arch_BAD', audit_SL_items_with_arch_BAD)
    db_safe_edit(control_dic, 'audit_SL_items_without_arch', audit_SL_items_without_arch)
    db_safe_edit(control_dic, 'audit_SL_items_with_arch_ROM', audit_SL_items_with_arch_ROM)
    db_safe_edit(control_dic, 'audit_SL_items_with_arch_ROM_OK', audit_SL_items_with_arch_ROM_OK)
    db_safe_edit(control_dic, 'audit_SL_items_with_arch_ROM_BAD', audit_SL_items_with_arch_ROM_BAD)
    db_safe_edit(control_dic, 'audit_SL_items_without_arch_ROM', audit_SL_items_without_arch_ROM)
    db_safe_edit(control_dic, 'audit_SL_items_with_CHD', audit_SL_items_with_CHD)
    db_safe_edit(control_dic, 'audit_SL_items_with_CHD_OK', audit_SL_items_with_CHD_OK)
    db_safe_edit(control_dic, 'audit_SL_items_with_CHD_BAD', audit_SL_items_with_CHD_BAD)
    db_safe_edit(control_dic, 'audit_SL_items_without_CHD', audit_SL_items_without_CHD)

    # Update timestamp and save control_dic.
    db_safe_edit(control_dic, 't_SL_audit', time.time())
    utils_write_JSON_file(cfg.MAIN_CONTROL_PATH.getPath(), control_dic)

# -------------------------------------------------------------------------------------------------
# MAME database building
# -------------------------------------------------------------------------------------------------
# 1) Scan MAME hash dir for XML files.
# 2) For each XML file, read the first XML_READ_LINES lines.
# 3) Search for the line <softwarelist name="32x" description="Sega 32X cartridges">
# 4) Create the file SL_NAMES_PATH with a dictionary {sl_name : description, ... }
#
# <softwarelist name="32x" description="Sega 32X cartridges">
# <softwarelist name="vsmile_cart" description="VTech V.Smile cartridges">
# <softwarelist name="vsmileb_cart" description="VTech V.Smile Baby cartridges">
def mame_build_SL_names(cfg):
    XML_READ_LINES = 600
    log_debug('mame_build_SL_names() Starting...')

    # If MAME hash path is not configured then create and empty file
    SL_names_dic = {}
    hash_dir_FN = FileName(cfg.settings['SL_hash_path'])
    if not hash_dir_FN.exists():
        log_info('mame_build_SL_names() MAME hash path does not exists.')
        log_info('mame_build_SL_names() Creating empty SL_NAMES_PATH')
        utils_write_JSON_file(cfg.SL_NAMES_PATH.getPath(), SL_names_dic)
        return

    # MAME hash path exists. Carry on.
    file_list = os.listdir(hash_dir_FN.getPath())
    log_debug('mame_build_SL_names() Found {} files'.format(len(file_list)))
    xml_files = []
    for file in file_list:
        if file.endswith('.xml'): xml_files.append(file)
    log_debug('mame_build_SL_names() Found {} XML files'.format(len(xml_files)))
    for f_name in xml_files:
        XML_FN = hash_dir_FN.pjoin(f_name)
        # log_debug('Inspecting file "{}"'.format(XML_FN.getPath()))
        # Read first XML_READ_LINES lines
        try:
            f = io.open(XML_FN.getPath(), 'r', encoding = 'utf-8')
        except IOError:
            log_error('(IOError) Exception opening {}'.format(XML_FN.getPath()))
            continue
        # f.readlines(XML_READ_LINES) does not work well for some files
        # content_list = f.readlines(XML_READ_LINES)
        line_count = 1
        content_list = []
        try:
            for line in f:
                content_list.append(line)
                line_count += 1
                if line_count > XML_READ_LINES: break
        except UnicodeDecodeError as ex:
            log_error('Exception UnicodeDecodeError on line {} of file "{}"'.format(line_count, XML_FN.getBase()))
            log_error('Previous line "{}"'.format(content_list[-1]))
            raise TypeError
        f.close()
        content_list = [x.strip() for x in content_list]
        for line in content_list:
            # Search for SL name
            if not line.startswith('<softwarelist'): continue
            m = re.search(r'<softwarelist name="([^"]+?)" description="([^"]+?)"', line)
            if not m: continue
            SL_name, SL_desc = m.group(1), m.group(2)
            # log_debug('SL "{}" -> "{}"'.format(SL_name, SL_desc))
            # Substitute SL description (long name).
            if SL_desc in SL_better_name_dic:
                old_SL_desc = SL_desc
                SL_desc = SL_better_name_dic[SL_desc]
                log_debug('Substitute SL "{}" with "{}"'.format(old_SL_desc, SL_desc))
            SL_names_dic[SL_name] = SL_desc
            break
    # Save database
    log_debug('mame_build_SL_names() Extracted {} Software List names'.format(len(SL_names_dic)))
    utils_write_JSON_file(cfg.SL_NAMES_PATH.getPath(), SL_names_dic)

# -------------------------------------------------------------------------------------------------
# Reads and processes MAME.xml
#
# The ROM location in the non-merged set is unique and can be used as a unique dictionary key.
# Include only ROMs and not CHDs.
#
# roms_sha1_dic = {
#     rom_nonmerged_location_1 : sha1_hash,
#     rom_nonmerged_location_2 : sha1_hash,
#     ...
#
# }
#
# Saves:
#   MAIN_DB_PATH
#   RENDER_DB_PATH
#   ROMS_DB_PATH
#   MAIN_ASSETS_DB_PATH  (empty JSON file)
#   MAIN_PCLONE_DIC_PATH
#   MAIN_CONTROL_PATH    (updated and then JSON file saved)
#   ROM_SHA1_HASH_DB_PATH
#
def _get_stats_dic():
    return {
        'parents' : 0,
        'clones' : 0,
        'devices' : 0,
        'devices_parents' : 0,
        'devices_clones' : 0,
        'runnable' : 0,
        'runnable_parents' : 0,
        'runnable_clones' : 0,
        'samples' : 0,
        'samples_parents' : 0,
        'samples_clones' : 0,
        'BIOS' : 0,
        'BIOS_parents' : 0,
        'BIOS_clones' : 0,
        'coin' : 0,
        'coin_parents' : 0,
        'coin_clones' : 0,
        'nocoin' : 0,
        'nocoin_parents' : 0,
        'nocoin_clones' : 0,
        'mechanical' : 0,
        'mechanical_parents' : 0,
        'mechanical_clones' : 0,
        'dead' : 0,
        'dead_parents' : 0,
        'dead_clones' : 0,
    }

def _update_stats(stats, machine, m_render, runnable):
    if m_render['cloneof']: stats['clones'] += 1
    else:                   stats['parents'] += 1
    if m_render['isDevice']:
        stats['devices'] += 1
        if m_render['cloneof']:
            stats['devices_clones'] += 1
        else:
            stats['devices_parents'] += 1
    if runnable:
        stats['runnable'] += 1
        if m_render['cloneof']:
            stats['runnable_clones'] += 1
        else:
            stats['runnable_parents'] += 1
    if machine['sampleof']:
        stats['samples'] += 1
        if m_render['cloneof']:
            stats['samples_clones'] += 1
        else:
            stats['samples_parents'] += 1
    if m_render['isBIOS']:
        stats['BIOS'] += 1
        if m_render['cloneof']:
            stats['BIOS_clones'] += 1
        else:
            stats['BIOS_parents'] += 1

    if runnable:
        if machine['input']['att_coins'] > 0:
            stats['coin'] += 1
            if m_render['cloneof']:
                stats['coin_clones'] += 1
            else:
                stats['coin_parents'] += 1
        else:
            stats['nocoin'] += 1
            if m_render['cloneof']:
                stats['nocoin_clones'] += 1
            else:
                stats['nocoin_parents'] += 1
        if machine['isMechanical']:
            stats['mechanical'] += 1
            if m_render['cloneof']:
                stats['mechanical_clones'] += 1
            else:
                stats['mechanical_parents'] += 1
        if machine['isDead']:
            stats['dead'] += 1
            if m_render['cloneof']:
                stats['dead_clones'] += 1
            else:
                stats['dead_parents'] += 1

def mame_build_MAME_main_database(cfg, st_dic):
    # Use for debug purposes. This number must be much bigger than the actual number of machines
    # when releasing.
    STOP_AFTER_MACHINES = 250000
    DATS_dir_FN = FileName(cfg.settings['dats_path'])
    ALLTIME_FN = DATS_dir_FN.pjoin(ALLTIME_INI)
    ARTWORK_FN = DATS_dir_FN.pjoin(ARTWORK_INI)
    BESTGAMES_FN = DATS_dir_FN.pjoin(BESTGAMES_INI)
    CATEGORY_FN = DATS_dir_FN.pjoin(CATEGORY_INI)
    CATLIST_FN = DATS_dir_FN.pjoin(CATLIST_INI)
    CATVER_FN = DATS_dir_FN.pjoin(CATVER_INI)
    GENRE_FN = DATS_dir_FN.pjoin(GENRE_INI)
    MATURE_FN = DATS_dir_FN.pjoin(MATURE_INI)
    NPLAYERS_FN = DATS_dir_FN.pjoin(NPLAYERS_INI)
    SERIES_FN = DATS_dir_FN.pjoin(SERIES_INI)
    COMMAND_FN = DATS_dir_FN.pjoin(COMMAND_DAT)
    GAMEINIT_FN = DATS_dir_FN.pjoin(GAMEINIT_DAT)
    HISTORY_XML_FN = DATS_dir_FN.pjoin(HISTORY_XML)
    HISTORY_DAT_FN = DATS_dir_FN.pjoin(HISTORY_DAT)
    MAMEINFO_FN = DATS_dir_FN.pjoin(MAMEINFO_DAT)

    # --- Print user configuration for debug ---
    if cfg.settings['op_mode'] == OP_MODE_VANILLA:
        rom_path = cfg.settings['rom_path_vanilla']
    elif cfg.settings['op_mode'] == OP_MODE_RETRO_MAME2003PLUS:
        rom_path = cfg.settings['rom_path_2003_plus']
    else:
        raise TypeError('Unknown op_mode "{}"'.format(cfg.settings['op_mode']))
    log_info('mame_build_MAME_main_database() Starting...')
    log_info('--- Paths ---')
    log_info('mame_prog      = "{}"'.format(cfg.settings['mame_prog']))
    log_info('ROM path       = "{}"'.format(rom_path))
    log_info('assets_path    = "{}"'.format(cfg.settings['assets_path']))
    log_info('DATs_path      = "{}"'.format(cfg.settings['dats_path']))
    log_info('CHD_path       = "{}"'.format(cfg.settings['chd_path']))
    log_info('samples_path   = "{}"'.format(cfg.settings['samples_path']))
    log_info('SL_hash_path   = "{}"'.format(cfg.settings['SL_hash_path']))
    log_info('SL_rom_path    = "{}"'.format(cfg.settings['SL_rom_path']))
    log_info('SL_chd_path    = "{}"'.format(cfg.settings['SL_chd_path']))
    log_info('--- INI paths ---')
    log_info('alltime_path   = "{}"'.format(ALLTIME_FN.getPath()))
    log_info('artwork_path   = "{}"'.format(ARTWORK_FN.getPath()))
    log_info('bestgames_path = "{}"'.format(BESTGAMES_FN.getPath()))
    log_info('category_path  = "{}"'.format(CATEGORY_FN.getPath()))
    log_info('catlist_path   = "{}"'.format(CATLIST_FN.getPath()))
    log_info('catver_path    = "{}"'.format(CATVER_FN.getPath()))
    log_info('genre_path     = "{}"'.format(GENRE_FN.getPath()))
    log_info('mature_path    = "{}"'.format(MATURE_FN.getPath()))
    log_info('nplayers_path  = "{}"'.format(NPLAYERS_FN.getPath()))
    log_info('series_path    = "{}"'.format(SERIES_FN.getPath()))
    log_info('--- DAT paths ---')
    log_info('command_path     = "{}"'.format(COMMAND_FN.getPath()))
    log_info('gameinit_path    = "{}"'.format(GAMEINIT_FN.getPath()))
    log_info('history_xml_path = "{}"'.format(HISTORY_XML_FN.getPath()))
    log_info('history_dat_path = "{}"'.format(HISTORY_DAT_FN.getPath()))
    log_info('mameinfo_path    = "{}"'.format(MAMEINFO_FN.getPath()))

    # --- Automatically extract and/or process MAME XML ---
    # After this block of code we have:
    # 1) a valid XML_control_dic and the XML control file is created and/or current.
    # 2) valid and verified for existence MAME_XML_path.
    MAME_XML_path, XML_control_FN = mame_init_MAME_XML(cfg, st_dic)
    if st_dic['abort']: return
    XML_control_dic = utils_load_JSON_file(XML_control_FN.getPath())

    # Main progress dialog.
    pDialog = KodiProgressDialog()

    # --- Build SL_NAMES_PATH if available, to be used later in the catalog building ---
    if cfg.settings['global_enable_SL']:
        pDialog.startProgress('Creating list of Software List names...')
        mame_build_SL_names(cfg)
        pDialog.endProgress()
    else:
        log_info('SL globally disabled, not creating SL names.')

    # --- Load INI files to include category information ---
    num_items = 10
    pd_line1 = 'Processing INI files...'
    pDialog.startProgress(pd_line1, num_items)
    pDialog.updateProgress(0, '{}\nFile {}'.format(pd_line1, ALLTIME_INI))
    alltime_dic = mame_load_INI_datfile_simple(ALLTIME_FN.getPath())
    pDialog.updateProgress(1, '{}\nFile {}'.format(pd_line1, ARTWORK_INI))
    artwork_dic = mame_load_INI_datfile_simple(ARTWORK_FN.getPath())
    pDialog.updateProgress(2, '{}\nFile {}'.format(pd_line1, BESTGAMES_INI))
    bestgames_dic = mame_load_INI_datfile_simple(BESTGAMES_FN.getPath())
    pDialog.updateProgress(3, '{}\nFile {}'.format(pd_line1, CATEGORY_INI))
    category_dic = mame_load_INI_datfile_simple(CATEGORY_FN.getPath())
    pDialog.updateProgress(4, '{}\nFile {}'.format(pd_line1, CATLIST_INI))
    catlist_dic = mame_load_INI_datfile_simple(CATLIST_FN.getPath())
    pDialog.updateProgress(5, '{}\nFile {}'.format(pd_line1, CATVER_INI))
    (catver_dic, veradded_dic) = mame_load_Catver_ini(CATVER_FN.getPath())
    pDialog.updateProgress(6, '{}\nFile {}'.format(pd_line1, GENRE_INI))
    genre_dic = mame_load_INI_datfile_simple(GENRE_FN.getPath())
    pDialog.updateProgress(7, '{}\nFile {}'.format(pd_line1, MATURE_INI))
    mature_dic = mame_load_Mature_ini(MATURE_FN.getPath())
    pDialog.updateProgress(8, '{}\nFile {}'.format(pd_line1, NPLAYERS_INI))
    nplayers_dic = mame_load_nplayers_ini(NPLAYERS_FN.getPath())
    pDialog.updateProgress(9, '{}\nFile {}'.format(pd_line1, SERIES_INI))
    series_dic = mame_load_INI_datfile_simple(SERIES_FN.getPath())
    pDialog.endProgress()

    # --- Load DAT files to include category information ---
    num_items = 4
    pd_line1 = 'Processing DAT files...'
    pDialog.startProgress(pd_line1, num_items)
    pDialog.updateProgress(0, '{}\nFile {}'.format(pd_line1, COMMAND_DAT))
    command_dic = mame_load_Command_DAT(COMMAND_FN.getPath())
    pDialog.updateProgress(1, '{}\nFile {}'.format(pd_line1, GAMEINIT_DAT))
    gameinit_dic = mame_load_GameInit_DAT(GAMEINIT_FN.getPath())
    # First try to load History.xml. If not found, then try History.dat
    if HISTORY_XML_FN.exists():
        pDialog.updateProgress(2, '{}\nFile {}'.format(pd_line1, HISTORY_XML))
        history_dic = mame_load_History_xml(HISTORY_XML_FN.getPath())
    else:
        pDialog.updateProgress(2, '{}\nFile {}'.format(pd_line1, HISTORY_DAT))
        history_dic = mame_load_History_DAT(HISTORY_DAT_FN.getPath())
    pDialog.updateProgress(3, '{}\nFile {}'.format(pd_line1, MAMEINFO_DAT))
    mameinfo_dic = mame_load_MameInfo_DAT(MAMEINFO_FN.getPath())
    pDialog.endProgress()

    # --- Verify that INIs comply with the data model ---
    # In MAME 0.209 only artwork, category and series are lists. Other INIs define
    # machine-unique categories (each machine belongs to one category only).
    log_info('alltime_dic   unique_categories {}'.format(alltime_dic['unique_categories']))
    log_info('artwork_dic   unique_categories {}'.format(artwork_dic['unique_categories']))
    log_info('bestgames_dic unique_categories {}'.format(bestgames_dic['unique_categories']))
    log_info('category_dic  unique_categories {}'.format(category_dic['unique_categories']))
    log_info('catlist_dic   unique_categories {}'.format(catlist_dic['unique_categories']))
    log_info('catver_dic    unique_categories {}'.format(catver_dic['unique_categories']))
    log_info('genre_dic     unique_categories {}'.format(genre_dic['unique_categories']))
    log_info('mature_dic    unique_categories {}'.format(mature_dic['unique_categories']))
    log_info('nplayers_dic  unique_categories {}'.format(nplayers_dic['unique_categories']))
    log_info('series_dic    unique_categories {}'.format(series_dic['unique_categories']))
    log_info('veradded_dic  unique_categories {}'.format(veradded_dic['unique_categories']))

    # ---------------------------------------------------------------------------------------------
    # Incremental Parsing approach B (from [1])
    # ---------------------------------------------------------------------------------------------
    # Do not load whole MAME XML into memory! Use an iterative parser to
    # grab only the information we want and discard the rest.
    # See [1] http://effbot.org/zone/element-iterparse.htm
    log_info('Loading XML "{}"'.format(MAME_XML_path.getPath()))
    xml_iter = ET.iterparse(MAME_XML_path.getPath(), events = ("start", "end"))
    event, root = next(xml_iter)
    if cfg.settings['op_mode'] == OP_MODE_VANILLA:
        mame_version_str = root.attrib['build']
        mame_version_int = mame_get_numerical_version(mame_version_str)
    elif cfg.settings['op_mode'] == OP_MODE_RETRO_MAME2003PLUS:
        mame_version_str = '0.78 (RA2003Plus)'
        mame_version_int = mame_get_numerical_version(mame_version_str)
    else:
        raise ValueError
    log_info('mame_build_MAME_main_database() MAME string version "{}"'.format(mame_version_str))
    log_info('mame_build_MAME_main_database() MAME numerical version {}'.format(mame_version_int))

    # --- Process MAME XML ---
    total_machines = XML_control_dic['total_machines']
    processed_machines = 0
    pDialog.startProgress('Building main MAME database...', total_machines)
    stats = _get_stats_dic()
    log_info('mame_build_MAME_main_database() total_machines {:,}'.format(total_machines))
    machines, renderdb_dic, machines_roms, machines_devices = {}, {}, {}, {}
    roms_sha1_dic = {}
    log_info('mame_build_MAME_main_database() Parsing MAME XML file ...')
    num_iteration = 0
    for event, elem in xml_iter:
        # Debug the elements we are iterating from the XML file
        # log_debug('event "{}"'.format(event))
        # log_debug('elem.tag "{}" | elem.text "{}" | elem.attrib "{}"'.format(elem.tag, elem.text, text_type(elem.attrib)))

        # <machine> tag start event includes <machine> attributes
        if event == 'start' and (elem.tag == 'machine' or elem.tag == 'game'):
            processed_machines += 1
            machine  = db_new_machine_dic()
            m_render = db_new_machine_render_dic()
            m_roms   = db_new_roms_object()
            device_list = []
            runnable = False
            num_displays = 0

            # --- Process <machine> attributes ----------------------------------------------------
            # name is #REQUIRED attribute
            if 'name' not in elem.attrib:
                log_error('name attribute not found in <machine> tag.')
                raise ValueError('name attribute not found in <machine> tag')
            m_name = elem.attrib['name']

            # In modern MAME sourcefile attribute is always present
            if cfg.settings['op_mode'] == OP_MODE_VANILLA:
                # sourcefile #IMPLIED attribute
                if 'sourcefile' not in elem.attrib:
                    log_error('sourcefile attribute not found in <machine> tag.')
                    raise ValueError('sourcefile attribute not found in <machine> tag.')
                # Remove trailing '.cpp' from driver name
                machine['sourcefile'] = elem.attrib['sourcefile']
            # In MAME 2003 Plus sourcefile attribute does not exists.
            elif cfg.settings['op_mode'] == OP_MODE_RETRO_MAME2003PLUS:
                machine['sourcefile'] = '[ Not set ]'
            else:
                raise ValueError

            # Optional, default no
            if 'isbios' not in elem.attrib:
                m_render['isBIOS'] = False
            else:
                m_render['isBIOS'] = True if elem.attrib['isbios'] == 'yes' else False
            if 'isdevice' not in elem.attrib:
                m_render['isDevice'] = False
            else:
                m_render['isDevice'] = True if elem.attrib['isdevice'] == 'yes' else False
            if 'ismechanical' not in elem.attrib:
                machine['isMechanical'] = False
            else:
                machine['isMechanical'] = True if elem.attrib['ismechanical'] == 'yes' else False
            # Optional, default yes
            if 'runnable' not in elem.attrib:
                runnable = True
            else:
                runnable = False if elem.attrib['runnable'] == 'no' else True

            # cloneof is #IMPLIED attribute
            if 'cloneof' in elem.attrib: m_render['cloneof'] = elem.attrib['cloneof']

            # romof is #IMPLIED attribute
            if 'romof' in elem.attrib: machine['romof'] = elem.attrib['romof']

            # sampleof is #IMPLIED attribute
            if 'sampleof' in elem.attrib: machine['sampleof'] = elem.attrib['sampleof']

            # --- Add catver/catlist/genre ---
            machine['alltime'] = alltime_dic['data'][m_name] if m_name in alltime_dic['data'] else '[ Not set ]'
            machine['artwork'] = artwork_dic['data'][m_name] if m_name in artwork_dic['data'] else [ '[ Not set ]' ]
            machine['bestgames'] = bestgames_dic['data'][m_name] if m_name in bestgames_dic['data'] else '[ Not set ]'
            machine['category'] = category_dic['data'][m_name] if m_name in category_dic['data'] else [ '[ Not set ]' ]
            machine['catlist'] = catlist_dic['data'][m_name] if m_name in catlist_dic['data'] else '[ Not set ]'
            machine['catver'] = catver_dic['data'][m_name] if m_name in catver_dic['data'] else '[ Not set ]'
            machine['genre'] = genre_dic['data'][m_name] if m_name in genre_dic['data'] else '[ Not set ]'
            machine['series'] = series_dic['data'][m_name] if m_name in series_dic['data'] else [ '[ Not set ]' ]
            machine['veradded'] = veradded_dic['data'][m_name] if m_name in veradded_dic['data'] else '[ Not set ]'
            # Careful, nplayers goes into render database.
            m_render['nplayers'] = nplayers_dic['data'][m_name] if m_name in nplayers_dic['data'] else '[ Not set ]'

        elif event == 'start' and elem.tag == 'description':
            m_render['description'] = text_type(elem.text)

        elif event == 'start' and elem.tag == 'year':
            m_render['year'] = text_type(elem.text)

        elif event == 'start' and elem.tag == 'manufacturer':
            m_render['manufacturer'] = text_type(elem.text)

        # Check in machine has BIOS
        # <biosset> name and description attributes are mandatory
        elif event == 'start' and elem.tag == 'biosset':
            # --- Add BIOS to ROMS_DB_PATH ---
            bios = db_new_bios_dic()
            bios['name'] = text_type(elem.attrib['name'])
            bios['description'] = text_type(elem.attrib['description'])
            m_roms['bios'].append(bios)

        # Check in machine has ROMs
        # A) ROM is considered to be valid if SHA1 has exists.
        #    Are there ROMs with no sha1? There are a lot, for example
        #    machine 1941j <rom name="yi22b.1a" size="279" status="nodump" region="bboardplds" />
        #
        # B) A ROM is unique to that machine if the <rom> tag does not have the 'merge' attribute.
        #    For example, snes and snespal both have <rom> tags that point to exactly the same
        #    BIOS. However, in a split set only snes.zip ROM set exists.
        #    snes    -> <rom name="spc700.rom" size="64" crc="44bb3a40" ... >
        #    snespal -> <rom name="spc700.rom" merge="spc700.rom" size="64" crc="44bb3a40" ... >
        #
        # C) In AML, hasROM actually means "machine has it own ROMs not found somewhere else".
        elif event == 'start' and elem.tag == 'rom':
            # --- Research ---
            # if not 'sha1' in elem.attrib:
            #     raise GeneralError('ROM with no sha1 (machine {})'.format(machine_name))

            # --- Add BIOS to ROMS_DB_PATH ---
            rom = db_new_rom_dic()
            rom['name']  = text_type(elem.attrib['name'])
            rom['merge'] = text_type(elem.attrib['merge']) if 'merge' in elem.attrib else ''
            rom['bios']  = text_type(elem.attrib['bios']) if 'bios' in elem.attrib else ''
            rom['size']  = int(elem.attrib['size']) if 'size' in elem.attrib else 0
            rom['crc']   = text_type(elem.attrib['crc']) if 'crc' in elem.attrib else ''
            m_roms['roms'].append(rom)

            # --- ROMs SHA1 database ---
            sha1 = text_type(elem.attrib['sha1']) if 'sha1' in elem.attrib else ''
            # Only add valid ROMs, ignore invalid.
            if sha1:
                rom_nonmerged_location = m_name + '/' + rom['name']
                roms_sha1_dic[rom_nonmerged_location] = sha1

        # Check in machine has CHDs
        # A) CHD is considered valid if and only if SHA1 hash exists.
        #    Keep in mind that there can be multiple disks per machine, some valid, some invalid.
        #    Just one valid CHD is OK.
        # B) A CHD is unique to a machine if the <disk> tag does not have the 'merge' attribute.
        #    See comments for ROMs avobe.
        elif event == 'start' and elem.tag == 'disk':
            # <!ATTLIST disk name CDATA #REQUIRED>
            # if 'sha1' in elem.attrib and 'merge' in elem.attrib: machine['CHDs_merged'].append(elem.attrib['name'])
            # if 'sha1' in elem.attrib and 'merge' not in elem.attrib: machine['CHDs'].append(elem.attrib['name'])

            # Add BIOS to ROMS_DB_PATH.
            disk = db_new_disk_dic()
            disk['name']  = text_type(elem.attrib['name'])
            disk['merge'] = text_type(elem.attrib['merge']) if 'merge' in elem.attrib else ''
            disk['sha1']  = text_type(elem.attrib['sha1']) if 'sha1' in elem.attrib else ''
            m_roms['disks'].append(disk)

        # Machine devices
        elif event == 'start' and elem.tag == 'device_ref':
            device_list.append(text_type(elem.attrib['name']))

        # Machine samples
        elif event == 'start' and elem.tag == 'sample':
            sample = { 'name' : text_type(elem.attrib['name']) }
            m_roms['samples'].append(sample)

        # Chips define CPU and audio circuits.
        elif event == 'start' and elem.tag == 'chip':
            if elem.attrib['type'] == 'cpu':
                machine['chip_cpu_name'].append(elem.attrib['name'])

        # Some machines have more than one display tag (for example aquastge has 2).
        # Other machines have no display tag (18w)
        elif event == 'start' and elem.tag == 'display':
            rotate_str = elem.attrib['rotate'] if 'rotate' in elem.attrib else '0'
            width_str = elem.attrib['width'] if 'width' in elem.attrib else 'Undefined'
            height_str = elem.attrib['height'] if 'height' in elem.attrib else 'Undefined'
            # All attribute lists have same length, event if data is empty.
            # machine['display_tag'].append(elem.attrib['tag'])
            machine['display_type'].append(elem.attrib['type'])
            machine['display_rotate'].append(rotate_str)
            machine['display_width'].append(width_str)
            machine['display_height'].append(height_str)
            machine['display_refresh'].append(elem.attrib['refresh'])
            num_displays += 1

        # Some machines have no controls at all.
        # 1) <control> reqbuttons attribute, pang uses it (has 2 buttons but only 1 is required
        # 2) <control> reqbuttons ways2, bcclimbr uses it. Sometimes ways attribute is a string!
        #
        # machine['input'] = {
        #     'att_players' CDATA #REQUIRED
        #     'att_coins'   CDATA #IMPLIED
        #     'att_service' (yes|no) "no"
        #     'att_tilt'    (yes|no) "no"
        #     'control_list' : [
        #         {
        #             'type'    : string CDATA #REQUIRED
        #             'player'  : int CDATA #IMPLIED
        #             'buttons' : int CDATA #IMPLIED
        #             'ways'    : [ ways string, ways2 string, ways3 string ] CDATA #IMPLIED
        #         }, ...
        #     ]
        # }
        #
        # In MAME 2003 Plus bios machines are not runnable and only have <description>,
        # <year>, <manufacturer>, <biosset> and <rom> tags. For example, machine neogeo.
        #
        elif event == 'start' and elem.tag == 'input':
            # In the archaic MAMEs used by Retroarch the control structure is different
            # and this code must be adapted.
            vanilla_mame_input_mode = True

            # --- <input> attributes ---
            # Attribute list in the same order as in the DTD
            att_service = False
            if 'service' in elem.attrib and elem.attrib['service'] == 'yes':
                att_service = True
            att_tilt = False
            if 'tilt' in elem.attrib and elem.attrib['tilt'] == 'yes':
                att_tilt = True
            att_players = int(elem.attrib['players']) if 'players' in elem.attrib else 0
            # "control" attribute only in MAME 2003 Plus.
            # Note that in some machines with valid controls, for example 88games, <input> control
            # attribute is empty and must be given a default value.
            att_control = '[ Undefined control type ]'
            if 'control' in elem.attrib:
                vanilla_mame_input_mode = False
                att_control = elem.attrib['control']
            # "buttons" attribute only in MAME 2003 Plus.
            att_buttons = 0
            if 'buttons' in elem.attrib:
                vanilla_mame_input_mode = False
                att_buttons = int(elem.attrib['buttons'])
            att_coins = int(elem.attrib['coins']) if 'coins' in elem.attrib else 0

            # --- Create control_list ---
            control_list = []
            if vanilla_mame_input_mode:
                # --- Vanilla MAME mode ---
                # <input> child tags.
                for control_child in elem:
                    attrib = control_child.attrib
                    # Skip non <control> tags. Process <control> tags only.
                    if control_child.tag != 'control': continue
                    # Error test. "type" is the only required attribute.
                    if 'type' not in attrib:
                        raise TypeError('<input> -> <control> has not "type" attribute')
                    ctrl_dic = {'type' : '', 'player' : -1, 'buttons' : -1, 'ways' : []}
                    ctrl_dic['type'] = attrib['type']
                    ctrl_dic['player'] = int(attrib['player']) if 'player' in attrib else -1
                    ctrl_dic['buttons'] = int(attrib['buttons']) if 'buttons' in attrib else -1
                    ways_list = []
                    if 'ways'  in attrib: ways_list.append(attrib['ways'])
                    if 'ways2' in attrib: ways_list.append(attrib['ways2'])
                    if 'ways3' in attrib: ways_list.append(attrib['ways3'])
                    ctrl_dic['ways'] = ways_list
                    control_list.append(ctrl_dic)
                # Fix player field when implied.
                if att_players == 1:
                    for control in control_list: control['player'] = 1
            else:
                # --- MAME 2003 Plus mode ---
                # Create a simulated control_list.
                for i in range(att_players):
                    control_list.append({
                        'type' : att_control,
                        'player' : i + 1,
                        'buttons' : att_buttons,
                        'ways' : [],
                    })

            # Add new input dictionary.
            machine['input'] = {
                'att_service'  : att_service,
                'att_tilt'     : att_tilt,
                'att_players'  : att_players,
                'att_coins'    : att_coins,
                'control_list' : control_list,
            }

        elif event == 'start' and elem.tag == 'driver':
            # status is #REQUIRED attribute
            m_render['driver_status'] = text_type(elem.attrib['status'])

        elif event == 'start' and elem.tag == 'softwarelist':
            # name is #REQUIRED attribute
            machine['softwarelists'].append(elem.attrib['name'])

        # Device tag for machines that support loading external files
        elif event == 'start' and elem.tag == 'device':
            att_type      = elem.attrib['type'] # The only mandatory attribute
            att_tag       = elem.attrib['tag']       if 'tag'       in elem.attrib else ''
            att_mandatory = elem.attrib['mandatory'] if 'mandatory' in elem.attrib else ''
            att_interface = elem.attrib['interface'] if 'interface' in elem.attrib else ''
            # Transform device_mandatory into bool
            if att_mandatory and att_mandatory == '1': att_mandatory = True
            else:                                      att_mandatory = False

            # Iterate children of <device> and search for <instance> tags
            instance_tag_found = False
            inst_name = ''
            inst_briefname = ''
            ext_names = []
            for device_child in elem:
                if device_child.tag == 'instance':
                    # Stop if <device> tag has more than one <instance> tag. In MAME 0.190 no
                    # machines trigger this.
                    if instance_tag_found:
                        raise GeneralError('Machine {} has more than one <instance> inside <device>')
                    inst_name      = device_child.attrib['name']
                    inst_briefname = device_child.attrib['briefname']
                    instance_tag_found = True
                elif device_child.tag == 'extension':
                    ext_names.append(device_child.attrib['name'])

            # NOTE Some machines have no instance inside <device>, for example 2020bb
            #      I don't know how to launch those machines
            # if not instance_tag_found:
                # log_warning('<instance> tag not found inside <device> tag (machine {})'.format(m_name))
                # device_type = '{} (NI)'.format(device_type)

            # Add device to database
            device_dic = {
                'att_type'      : att_type,
                'att_tag'       : att_tag,
                'att_mandatory' : att_mandatory,
                'att_interface' : att_interface,
                'instance'      : { 'name' : inst_name, 'briefname' : inst_briefname },
                'ext_names'     : ext_names
            }
            machine['devices'].append(device_dic)

        # --- <machine>/<game> tag closing. Add new machine to database ---
        elif event == 'end' and (elem.tag == 'machine' or elem.tag == 'game'):
            # Checks in modern MAME
            if cfg.settings['op_mode'] == OP_MODE_VANILLA:
                # Assumption 1: isdevice = True if and only if runnable = False
                if m_render['isDevice'] == runnable:
                    log_error("Machine {}: machine['isDevice'] == runnable".format(m_name))
                    raise ValueError

                # Are there machines with more than 1 <display> tag. Answer: YES
                # if num_displays > 1:
                #     log_error("Machine {}: num_displays = {}".format(m_name, num_displays))
                #     raise ValueError

                # All machines with 0 displays are mechanical? NO, 24cdjuke has no screen and
                # is not mechanical. However 24cdjuke is a preliminary driver.
                # if num_displays == 0 and not machine['ismechanical']:
                #     log_error("Machine {}: num_displays == 0 and not machine['ismechanical']".format(m_name))
                #     raise ValueError
            # Checks in Retroarch MAME 2003 Plus
            elif cfg.settings['op_mode'] == OP_MODE_RETRO_MAME2003PLUS:
                # In MAME 2003 Plus XML some <year> tags are empty.
                # Set a default value.
                if not m_render['year']: m_render['year'] = '[ Not set ]'
            else:
                raise ValueError

            # Mark dead machines. A machine is dead if Status is preliminary AND have no controls.
            if m_render['driver_status'] == 'preliminary' and not machine['input']['control_list']:
                machine['isDead'] = True

            # --- Delete XML element once it has been processed to conserve memory ---
            elem.clear()

            # --- Compute statistics ---
            _update_stats(stats, machine, m_render, runnable)

            # Add new machine
            machines[m_name] = machine
            renderdb_dic[m_name] = m_render
            machines_roms[m_name] = m_roms
            machines_devices[m_name] = device_list

        # --- Print something to prove we are doing stuff ---
        num_iteration += 1
        if num_iteration % 1000 == 0:
            pDialog.updateProgress(processed_machines)
            # log_debug('Processed {:10d} events ({:6d} machines so far) ...'.format(
            #     num_iteration, processed_machines))
            # log_debug('processed_machines   = {}'.format(processed_machines))
            # log_debug('total_machines = {}'.format(total_machines))
        # Stop after STOP_AFTER_MACHINES machines have been processed for debug.
        if processed_machines >= STOP_AFTER_MACHINES: break
    pDialog.endProgress()
    log_info('Processed {:,} MAME XML events'.format(num_iteration))
    log_info('Processed machines {:,} ({:,} parents, {:,} clones)'.format(
        processed_machines, stats['parents'], stats['clones']))
    log_info('Dead machines      {:,} ({:,} parents, {:,} clones)'.format(
        stats['dead'], stats['dead_parents'], stats['dead_clones']))

    # ---------------------------------------------------------------------------------------------
    # Main parent-clone list
    # ---------------------------------------------------------------------------------------------
    # Create a couple of data struct for quickly know the parent of a clone game and
    # all clones of a parent.
    # main_pclone_dic          = { 'parent_name' : ['clone_name', 'clone_name', ... ] , ... }
    # main_clone_to_parent_dic = { 'clone_name' : 'parent_name', ... }
    log_info('Making PClone list...')
    main_pclone_dic = {}
    main_clone_to_parent_dic = {}
    for machine_name in renderdb_dic:
        m_render = renderdb_dic[machine_name]
        if m_render['cloneof']:
            parent_name = m_render['cloneof']
            # If parent already in main_pclone_dic then add clone to parent list.
            # If parent not there, then add parent first and then add clone.
            if parent_name not in main_pclone_dic: main_pclone_dic[parent_name] = []
            main_pclone_dic[parent_name].append(machine_name)
            # Add clone machine to main_clone_to_parent_dic
            main_clone_to_parent_dic[machine_name] = parent_name
            continue
        # Machine is a parent. Add to main_pclone_dic if not already there.
        if machine_name not in main_pclone_dic: main_pclone_dic[machine_name] = []

    # ---------------------------------------------------------------------------------------------
    # Initialise asset list
    # ---------------------------------------------------------------------------------------------
    log_debug('Initializing MAME asset database...')
    log_debug('Option generate_history_infolabel is {}'.format(cfg.settings['generate_history_infolabel']))
    assetdb_dic = {key : db_new_MAME_asset() for key in machines}
    if cfg.settings['generate_history_infolabel'] and history_idx_dic:
        log_debug('Adding History.DAT to MAME asset database.')
        for m_name in assetdb_dic:
            asset = assetdb_dic[m_name]
            asset['flags'] = db_initial_flags(machines[m_name], renderdb_dic[m_name], machines_roms[m_name])
            if m_name in history_idx_dic['mame']['machines']:
                d_name, db_list, db_machine = history_idx_dic['mame']['machines'][m_name].split('|')
                asset['history'] = history_dic[db_list][db_machine]
    else:
        log_debug('Not including History.DAT in MAME asset database.')
        for m_name in assetdb_dic:
            assetdb_dic[m_name]['flags'] = db_initial_flags(machines[m_name],
                renderdb_dic[m_name], machines_roms[m_name])

    # ---------------------------------------------------------------------------------------------
    # Improve information fields in Main Render database
    # ---------------------------------------------------------------------------------------------
    if mature_dic:
        log_info('MAME machine Mature information available.')
        for machine_name in renderdb_dic:
            renderdb_dic[machine_name]['isMature'] = True if machine_name in mature_dic['data'] else False
    else:
        log_info('MAME machine Mature flag not available.')

    # Add genre infolabel into render database.
    if genre_dic:
        log_info('Using genre.ini for MAME genre information.')
        for machine_name in renderdb_dic:
            renderdb_dic[machine_name]['genre'] = machines[machine_name]['genre']
    elif categories_dic:
        log_info('Using catver.ini for MAME genre information.')
        for machine_name in renderdb_dic:
            renderdb_dic[machine_name]['genre'] = machines[machine_name]['catver']
    elif catlist_dic:
        log_info('Using catlist.ini for MAME genre information.')
        for machine_name in renderdb_dic:
            renderdb_dic[machine_name]['genre'] = machines[machine_name]['catlist']

    # ---------------------------------------------------------------------------------------------
    # Improve name in DAT indices and machine names
    # ---------------------------------------------------------------------------------------------
    # --- History DAT categories are Software List names ---
    if history_dic:
        log_debug('Updating History DAT categories and machine names ...')
        SL_names_dic = utils_load_JSON_file(cfg.SL_NAMES_PATH.getPath())
        for cat_name in history_dic['index']:
            if cat_name == 'mame':
                # Improve MAME machine names
                history_dic['index'][cat_name]['name'] = 'MAME'
                for machine_name in history_dic['index'][cat_name]['machines']:
                    if machine_name not in renderdb_dic: continue
                    # Rebuild the CSV string.
                    m_str = history_dic['index'][cat_name]['machines'][machine_name]
                    old_display_name, db_list_name, db_machine_name = m_str.split('|')
                    display_name = renderdb_dic[machine_name]['description']
                    m_str = misc_build_db_str_3(display_name, db_list_name, db_machine_name)
                    history_dic['index'][cat_name]['machines'][machine_name] = m_str
            elif cat_name in SL_names_dic:
                # Improve SL machine names. This must be done when building the SL databases
                # and not here.
                history_dic['index'][cat_name]['name'] = SL_names_dic[cat_name]

    # MameInfo DAT machine names.
    if mameinfo_dic['index']:
        log_debug('Updating Mameinfo DAT machine names ...')
        for cat_name in mameinfo_dic['index']:
            for machine_key in mameinfo_dic['index'][cat_name]:
                if machine_key not in renderdb_dic: continue
                mameinfo_dic['index'][cat_name][machine_key] = renderdb_dic[machine_key]['description']

    # GameInit DAT machine names.
    if gameinit_dic['index']:
        log_debug('Updating GameInit DAT machine names ...')
        for machine_key in gameinit_dic['index']:
            if machine_key not in renderdb_dic: continue
            gameinit_dic['index'][machine_key] = renderdb_dic[machine_key]['description']

    # Command DAT machine names.
    if command_dic['index']:
        log_debug('Updating Command DAT machine names ...')
        for machine_key in command_dic['index']:
            if machine_key not in renderdb_dic: continue
            command_dic['index'][machine_key] = renderdb_dic[machine_key]['description']

    # ---------------------------------------------------------------------------------------------
    # Update/Reset MAME control dictionary
    # Create a new control_dic. This effectively resets AML status.
    # The XML control file is required to create the new control_dic.
    # ---------------------------------------------------------------------------------------------
    log_info('Creating new control_dic.')
    log_info('AML version string "{}"'.format(cfg.addon.info_version))
    log_info('AML version int {}'.format(cfg.addon_version_int))
    control_dic = db_new_control_dic()
    db_safe_edit(control_dic, 'op_mode_raw', cfg.settings['op_mode_raw'])
    db_safe_edit(control_dic, 'op_mode', cfg.settings['op_mode'])

    # Information from the XML control file.
    db_safe_edit(control_dic, 'stats_total_machines', total_machines)

    # Addon and MAME version strings
    db_safe_edit(control_dic, 'ver_AML_str', cfg.addon.info_version)
    db_safe_edit(control_dic, 'ver_AML_int', cfg.addon_version_int)
    db_safe_edit(control_dic, 'ver_mame_str', mame_version_str)
    db_safe_edit(control_dic, 'ver_mame_int', mame_version_int)
    # INI files
    db_safe_edit(control_dic, 'ver_alltime', alltime_dic['version'])
    db_safe_edit(control_dic, 'ver_artwork', artwork_dic['version'])
    db_safe_edit(control_dic, 'ver_bestgames', bestgames_dic['version'])
    db_safe_edit(control_dic, 'ver_category', category_dic['version'])
    db_safe_edit(control_dic, 'ver_catlist', catlist_dic['version'])
    db_safe_edit(control_dic, 'ver_catver', catver_dic['version'])
    db_safe_edit(control_dic, 'ver_genre', genre_dic['version'])
    db_safe_edit(control_dic, 'ver_mature', mature_dic['version'])
    db_safe_edit(control_dic, 'ver_nplayers', nplayers_dic['version'])
    db_safe_edit(control_dic, 'ver_series', series_dic['version'])
    # DAT files
    db_safe_edit(control_dic, 'ver_command', command_dic['version'])
    db_safe_edit(control_dic, 'ver_gameinit', gameinit_dic['version'])
    db_safe_edit(control_dic, 'ver_history', history_dic['version'])
    db_safe_edit(control_dic, 'ver_mameinfo', mameinfo_dic['version'])

    # Statistics
    db_safe_edit(control_dic, 'stats_processed_machines', processed_machines)
    db_safe_edit(control_dic, 'stats_parents', stats['parents'])
    db_safe_edit(control_dic, 'stats_clones', stats['clones'])
    db_safe_edit(control_dic, 'stats_runnable', stats['runnable'])
    db_safe_edit(control_dic, 'stats_runnable_parents', stats['runnable_parents'])
    db_safe_edit(control_dic, 'stats_runnable_clones', stats['runnable_clones'])
    # Main filters
    db_safe_edit(control_dic, 'stats_coin', stats['coin'])
    db_safe_edit(control_dic, 'stats_coin_parents', stats['coin_parents'])
    db_safe_edit(control_dic, 'stats_coin_clones', stats['coin_clones'])
    db_safe_edit(control_dic, 'stats_nocoin', stats['nocoin'])
    db_safe_edit(control_dic, 'stats_nocoin_parents', stats['nocoin_parents'])
    db_safe_edit(control_dic, 'stats_nocoin_clones', stats['nocoin_clones'])
    db_safe_edit(control_dic, 'stats_mechanical', stats['mechanical'])
    db_safe_edit(control_dic, 'stats_mechanical_parents', stats['mechanical_parents'])
    db_safe_edit(control_dic, 'stats_mechanical_clones', stats['mechanical_clones'])
    db_safe_edit(control_dic, 'stats_dead', stats['dead'])
    db_safe_edit(control_dic, 'stats_dead_parents', stats['dead_parents'])
    db_safe_edit(control_dic, 'stats_dead_clones', stats['dead_clones'])
    db_safe_edit(control_dic, 'stats_devices', stats['devices'])
    db_safe_edit(control_dic, 'stats_devices_parents', stats['devices_parents'])
    db_safe_edit(control_dic, 'stats_devices_clones', stats['devices_clones'])
    # Binary filters
    db_safe_edit(control_dic, 'stats_BIOS', stats['BIOS'])
    db_safe_edit(control_dic, 'stats_BIOS_parents', stats['BIOS_parents'])
    db_safe_edit(control_dic, 'stats_BIOS_clones', stats['BIOS_clones'])
    db_safe_edit(control_dic, 'stats_samples', stats['samples'])
    db_safe_edit(control_dic, 'stats_samples_parents', stats['samples_parents'])
    db_safe_edit(control_dic, 'stats_samples_clones', stats['samples_clones'])

    # --- Timestamp ---
    db_safe_edit(control_dic, 't_MAME_DB_build', time.time())

    # ---------------------------------------------------------------------------------------------
    # Build main distributed hashed database
    # ---------------------------------------------------------------------------------------------
    # This saves the hash files in the database directory.
    # At this point the main hashed database is complete but the asset hashed DB is empty.
    db_build_main_hashed_db(cfg, control_dic, machines, renderdb_dic)
    db_build_asset_hashed_db(cfg, control_dic, assetdb_dic)

    # --- Save databases ---
    log_info('Saving database JSON files...')
    if OPTION_LOWMEM_WRITE_JSON:
        json_write_func = utils_write_JSON_file_lowmem
        log_debug('Using utils_write_JSON_file_lowmem() JSON writer')
    else:
        json_write_func = utils_write_JSON_file
        log_debug('Using utils_write_JSON_file() JSON writer')
    db_files = [
        [machines, 'MAME machines main', cfg.MAIN_DB_PATH.getPath()],
        [renderdb_dic, 'MAME render DB', cfg.RENDER_DB_PATH.getPath()],
        [assetdb_dic, 'MAME asset DB', cfg.ASSET_DB_PATH.getPath()],
        [machines_roms, 'MAME machine ROMs', cfg.ROMS_DB_PATH.getPath()],
        [machines_devices, 'MAME machine devices', cfg.DEVICES_DB_PATH.getPath()],
        [main_pclone_dic, 'MAME PClone dictionary', cfg.MAIN_PCLONE_DB_PATH.getPath()],
        [roms_sha1_dic, 'MAME ROMs SHA1 dictionary', cfg.SHA1_HASH_DB_PATH.getPath()],
        # --- DAT files ---
        [history_dic['index'], 'History DAT index', cfg.HISTORY_IDX_PATH.getPath()],
        [history_dic['data'], 'History DAT database', cfg.HISTORY_DB_PATH.getPath()],
        [mameinfo_dic['index'], 'MAMEInfo DAT index', cfg.MAMEINFO_IDX_PATH.getPath()],
        [mameinfo_dic['data'], 'MAMEInfo DAT database', cfg.MAMEINFO_DB_PATH.getPath()],
        [gameinit_dic['index'], 'Gameinit DAT index', cfg.GAMEINIT_IDX_PATH.getPath()],
        [gameinit_dic['data'], 'Gameinit DAT database', cfg.GAMEINIT_DB_PATH.getPath()],
        [command_dic['index'], 'Command DAT index', cfg.COMMAND_IDX_PATH.getPath()],
        [command_dic['data'], 'Command DAT database', cfg.COMMAND_DB_PATH.getPath()],
        # --- Save control_dic after everything is saved ---
        [control_dic, 'Control dictionary', cfg.MAIN_CONTROL_PATH.getPath()],
    ]
    db_save_files(db_files, json_write_func)

    # Return a dictionary with references to the objects just in case they are needed after
    # this function (in "Build everything", for example). This saves time, because databases do not
    # need to be reloaded, and apparently memory as well.
    return {
        'machines' : machines,
        'renderdb' : renderdb_dic,
        'assetdb' : assetdb_dic,
        'roms' : machines_roms,
        'devices' : machines_devices,
        'main_pclone_dic' : main_pclone_dic,
        'history_idx_dic' : history_dic['index'],
        'mameinfo_idx_dic' : mameinfo_dic['index'],
        'gameinit_idx_dic' : gameinit_dic['index'],
        'command_idx_dic' : command_dic['index'],
        'history_data_dic' : history_dic['data'],
        'control_dic' : control_dic,
    }

# -------------------------------------------------------------------------------------------------
# Generates the ROM audit database. This database contains invalid ROMs also to display information
# in "View / Audit", "View MAME machine ROMs" context menu. This database also includes
# device ROMs (<device_ref> ROMs).
def _get_ROM_type(rom):
    if       rom['bios'] and     rom['merge']: r_type = ROM_TYPE_BROM
    elif     rom['bios'] and not rom['merge']: r_type = ROM_TYPE_XROM
    elif not rom['bios'] and     rom['merge']: r_type = ROM_TYPE_MROM
    elif not rom['bios'] and not rom['merge']: r_type = ROM_TYPE_ROM
    else:                                      r_type = ROM_TYPE_ERROR
    return r_type

# Finds merged ROM merged_name in the parent ROM set roms (list of dictionaries).
# Returns a dictionary (first item of the returned list) or None if the merged ROM cannot
# be found in the ROMs of the parent.
def _get_merged_rom(roms, merged_name):
    merged_rom_list = [r for r in roms if r['name'] == merged_name]

    if len(merged_rom_list) > 0:
        return merged_rom_list[0]
    else:
        return None

# Traverses the ROM hierarchy and returns the ROM location and name.
def _get_ROM_location(rom_set, rom, m_name, machines, renderdb_dic, machine_roms):
    # In the Merged set all Parent and Clone ROMs are in the parent archive.
    # What about BIOS and Device ROMs?
    # However, according to the Pleasuredome DATs, ROMs are organised like
    # this:
    #   clone_name_a/clone_rom_1
    #   clone_name_b/clone_rom_1
    #   parent_rom_1
    #   parent_rom_2
    if rom_set == 'MERGED':
        cloneof = renderdb_dic[m_name]['cloneof']
        if cloneof:
            location = cloneof + '/' + m_name + '/' + rom['name']
        else:
            location = m_name + '/' + rom['name']

    elif rom_set == 'SPLIT':
        machine = machines[m_name]
        cloneof = renderdb_dic[m_name]['cloneof']
        if not cloneof:
            # --- Parent machine ---
            # 1. In the Split set non-merged ROMs are in the machine archive and merged ROMs
            #    are in the parent archive.
            if rom['merge']:
                romof = machine['romof']
                bios_name = romof
                bios_roms = machine_roms[bios_name]['roms']
                bios_rom_merged_name = rom['merge']
                bios_merged_rom = _get_merged_rom(bios_roms, bios_rom_merged_name)
                if bios_merged_rom['merge']:
                    bios_romof = machines[bios_name]['romof']
                    parent_bios_name = bios_romof
                    parent_bios_roms = machine_roms[parent_bios_name]['roms']
                    parent_bios_rom_merged_name = bios_merged_rom['merge']
                    parent_bios_merged_rom = _get_merged_rom(parent_bios_roms, parent_bios_rom_merged_name)
                    location = parent_bios_name + '/' + parent_bios_merged_rom['name']
                else:
                    location = bios_name + '/' + bios_merged_rom['name']
            else:
                location = m_name + '/' + rom['name']
        else:
            # --- Clone machine ---
            # 1. In the Split set, non-merged ROMs are in the machine ZIP archive and
            #    merged ROMs are in the parent archive.
            # 2. If ROM is a BIOS it is located in the romof of the parent. BIOS ROMs
            #    always have the merge attribute.
            # 3. Some machines (notably mslugN) also have non-BIOS common ROMs merged in
            #    neogeo.zip BIOS archive.
            # 4. Some machines (notably XXXXX) have all ROMs merged. In other words, do not
            #    have their own ROMs.
            # 5. Special case: there could be duplicate ROMs with different regions.
            #    For example, in neogeo.zip
            #    <rom name="sm1.sm1" size="131072" crc="94416d67" sha1="42f..." />
            #    <rom name="sm1.sm1" size="131072" crc="94416d67" sha1="42f..." />
            #
            #    Furthermore, some machines may have more than 2 identical ROMs:
            #    <machine name="aa3000" sourcefile="aa310.cpp" cloneof="aa310" romof="aa310">
            #    <rom name="cmos_riscos3.bin" merge="cmos_riscos3.bin" bios="300" size="256" crc="0da2d31d" />
            #    <rom name="cmos_riscos3.bin" merge="cmos_riscos3.bin" bios="310" size="256" crc="0da2d31d" />
            #    <rom name="cmos_riscos3.bin" merge="cmos_riscos3.bin" bios="311" size="256" crc="0da2d31d" />
            #    <rom name="cmos_riscos3.bin" merge="cmos_riscos3.bin" bios="319" size="256" crc="0da2d31d" />
            #
            # 6. In MAME 0.206, clone machine adonisce has a merged ROM 'setchip v4.04.09.u7'
            #    that is not found on the parent machine adoins ROMs.
            #        AML WARN : Clone machine "adonisce"
            #        AML WARN : ROM "setchip v4.04.09.u7" MERGE "setchip v4.04.09.u7"
            #        AML WARN : Cannot be found on parent "adonis" ROMs
            #    By looking to the XML, the ROM "setchip v4.04.09.u7" is on the BIOS aristmk5
            #    More machines with same issue: adonisu, bootsctnu, bootsctnua, bootsctnub, ...
            #    and a lot more machines related to BIOS aristmk5.
            #
            if rom['merge']:
                # >> Get merged ROM from parent
                parent_name = cloneof
                parent_roms = machine_roms[parent_name]['roms']
                clone_rom_merged_name = rom['merge']
                parent_merged_rom = _get_merged_rom(parent_roms, clone_rom_merged_name)
                # >> Clone merged ROM cannot be found in parent ROM set. This is likely a MAME
                # >> XML bug. In this case, treat the clone marged ROM as a non-merged ROM.
                if parent_merged_rom is None:
                    log_warning('Clone machine "{}" parent_merged_rom is None'.format(m_name))
                    log_warning('ROM "{}" MERGE "{}"'.format(rom['name'], rom['merge']))
                    log_warning('Cannot be found on parent "{}" ROMs'.format(parent_name))
                    # >> Check if merged ROM is in the BIOS machine.
                    bios_name = machines[parent_name]['romof']
                    if bios_name:
                        log_warning('Parent machine "{}" has BIOS machine "{}"'.format(parent_name, bios_name))
                        log_warning('Searching for clone merged ROM "{}" in BIOS ROMs'.format(clone_rom_merged_name))
                        bios_roms = machine_roms[bios_name]['roms']
                        bios_merged_rom = _get_merged_rom(bios_roms, clone_rom_merged_name)
                        location = bios_name + '/' + bios_merged_rom['name']
                    else:
                        TypeError
                # >> Check if clone merged ROM is also merged in parent (BIOS ROM)
                elif parent_merged_rom['merge']:
                    parent_romof = machines[parent_name]['romof']
                    bios_name = parent_romof
                    bios_roms = machine_roms[bios_name]['roms']
                    bios_rom_merged_name = parent_merged_rom['merge']
                    bios_merged_rom = _get_merged_rom(bios_roms, bios_rom_merged_name)
                    # At least in one machine (0.196) BIOS ROMs can be merged in another
                    # BIOS ROMs (1 level of recursion in BIOS ROM merging).
                    if bios_merged_rom['merge']:
                        bios_romof = machines[bios_name]['romof']
                        parent_bios_name = bios_romof
                        parent_bios_roms = machine_roms[parent_bios_name]['roms']
                        parent_bios_rom_merged_name = bios_merged_rom['merge']
                        parent_bios_merged_rom = _get_merged_rom(parent_bios_roms, parent_bios_rom_merged_name)
                        location = parent_bios_name + '/' + parent_bios_merged_rom['name']
                    else:
                        location = bios_name + '/' + bios_merged_rom['name']
                else:
                    location = parent_name + '/' + parent_merged_rom['name']
            else:
                location = m_name + '/' + rom['name']

    # In the Non-Merged set all ROMs are in the machine archive ZIP archive, with
    # the exception of BIOS ROMs and device ROMs.
    elif rom_set == 'NONMERGED':
        location = m_name + '/' + rom['name']

    # In the Fully Non-Merged sets all ROMs are in the machine ZIP archive, including
    # BIOS ROMs and device ROMs.
    # Note that PD ROM sets are named Non-Merged but actually they are Fully Non-merged.
    elif rom_set == 'FULLYNONMERGED':
        location = m_name + '/' + rom['name']

    else:
        raise TypeError

    return location

def _get_CHD_location(chd_set, disk, m_name, machines, renderdb_dic, machine_roms):
    if chd_set == 'MERGED':
        machine = machines[m_name]
        cloneof = renderdb_dic[m_name]['cloneof']
        romof   = machine['romof']
        if not cloneof:
            # --- Parent machine ---
            if disk['merge']:
                location = romof + '/' + disk['merge']
            else:
                location = m_name + '/' + disk['name']
        else:
            # --- Clone machine ---
            if disk['merge']:
                # Get merged ROM from parent
                parent_name = cloneof
                parent_romof = machines[parent_name]['romof']
                parent_disks =  machine_roms[parent_name]['disks']
                clone_disk_merged_name = disk['merge']
                # Pick ROMs with same name and choose the first one.
                parent_merged_disk_l = [r for r in parent_disks if r['name'] == clone_disk_merged_name]
                parent_merged_disk = parent_merged_disk_l[0]
                # Check if clone merged ROM is also merged in parent
                if parent_merged_disk['merge']:
                    # ROM is in the 'romof' archive of the parent ROM
                    super_parent_name = parent_romof
                    super_parent_disks =  machine_roms[super_parent_name]['disks']
                    parent_disk_merged_name = parent_merged_disk['merge']
                    # Pick ROMs with same name and choose the first one.
                    super_parent_merged_disk_l = [r for r in super_parent_disks if r['name'] == parent_disk_merged_name]
                    super_parent_merged_disk = super_parent_merged_disk_l[0]
                    location = super_parent_name + '/' + super_parent_merged_disk['name']
                else:
                    location = parent_name + '/' + parent_merged_disk['name']
            else:
                location = cloneof + '/' + disk['name']

    elif chd_set == 'SPLIT':
        machine = machines[m_name]
        cloneof = renderdb_dic[m_name]['cloneof']
        romof   = machine['romof']
        if not cloneof:
            # --- Parent machine ---
            if disk['merge']:
                location = romof + '/' + disk['name']
            else:
                location = m_name + '/' + disk['name']
        else:
            # --- Clone machine ---
            parent_romof = machines[cloneof]['romof']
            if disk['merge']:
                location = romof + '/' + disk['name']
            else:
                location = m_name + '/' + disk['name']

    elif chd_set == 'NONMERGED':
        location = m_name + '/' + disk['name']

    else:
        raise TypeError

    return location

# Returns a unique and alphabetically sorted list of ROM ZIP files.
# This list is different depending on the ROM set (Merged, Split or Non-merged).
def mame_get_ROM_ZIP_list(machine_archives_dic):
    rom_list = []
    for key, machine in machine_archives_dic.items():
        rom_list.extend(machine['ROMs'])

    return list(sorted(set(rom_list)))

def mame_get_Sample_ZIP_list(machine_archives_dic):
    rom_list = []
    for key, machine in machine_archives_dic.items():
        rom_list.extend(machine['Samples'])

    return list(sorted(set(rom_list)))

def mame_get_CHD_list(machine_archives_dic):
    rom_list = []
    for key, machine in machine_archives_dic.items():
        rom_list.extend(machine['CHDs'])

    return list(sorted(set(rom_list)))

#
# Checks for errors before scanning for SL ROMs.
# Display a Kodi dialog if an error is found.
# Returns a dictionary of settings:
# options_dic['abort'] is always present.
# 
#
def mame_check_before_build_ROM_audit_databases(cfg, st_dic, control_dic):
    kodi_reset_status(st_dic)

    # --- Check that MAME database have been built ---
    pass

#
# Builds the ROM/CHD/Samples audit database and more things.
# Updates statistics in control_dic and saves it.
# The audit databases changes for Merged, Split and Non-merged sets (the location of the ROMs changes).
# The audit database is used when auditing MAME machines.
#
# audit_roms_dic = {
#     'machine_name ' : [
#         {
#             'crc'      : string,
#             'location' : 'zip_name/rom_name.rom'
#             'name'     : string,
#             'size'     : int,
#             'type'     : 'ROM' or 'BROM' or 'MROM' or 'XROM'
#         }, ...,
#         {
#             'location' : 'machine_name/chd_name.chd'
#             'name'     : string,
#             'sha1'     : string,
#             'type'     : 'DISK'
#         }, ...,
#         {
#             'location' : 'machine_name/sample_name'
#             'name'     : string,
#             'type'     : 'SAM'
#         }, ...,
#     ], ...
# }
#
# This function also builds the machine files database.
#
# A) For every machine stores the ROM ZIP/CHD/Samples ZIP files required to run the machine.
# B) A ROM ZIP/CHD exists if and only if it has valid ROMs (CRC and SHA1 exist).
# C) Used by the ROM scanner to check how many machines may be run or not depending of the
#    ROM ZIPs/CHDs/Sample ZIPs you have.
# D) ROM ZIPs and CHDs are mandatory to run a machine. Samples are not. This function kind of
#    thinks that Samples are also mandatory.
#
# machine_archives_dic = {
#     'machine_name ' : {
#         'ROMs'    : [name1, name2, ...],
#         'CHDs'    : [dir/name1, dir/name2, ...],
#         'Samples' : [name1, name2, ...],
#     }, ...
# }
#
# Saved files:
#     ROM_AUDIT_DB_PATH
#     ROM_SET_MACHINE_FILES_DB_PATH
#     MAIN_CONTROL_PATH (control_dic)
#
# Add the following fields to db_dic_in:
#     audit_roms
#     machine_archives
#
def mame_build_ROM_audit_databases(cfg, st_dic, db_dic_in):
    log_info('mame_build_ROM_audit_databases() Initialising ...')
    control_dic = db_dic_in['control_dic']
    machines = db_dic_in['machines']
    renderdb_dic = db_dic_in['renderdb']
    devices_db_dic = db_dic_in['devices']
    machine_roms = db_dic_in['roms']

    # --- Initialize ---
    # This must match the values defined in settings.xml, "ROM sets" tab.
    rom_set = ['MERGED', 'SPLIT', 'NONMERGED', 'FULLYNONMERGED'][cfg.settings['mame_rom_set']]
    rom_set_str = ['Merged', 'Split', 'Non-merged', 'Fully Non-merged'][cfg.settings['mame_rom_set']]
    chd_set = ['MERGED', 'SPLIT', 'NONMERGED'][cfg.settings['mame_chd_set']]
    chd_set_str = ['Merged', 'Split', 'Non-merged'][cfg.settings['mame_chd_set']]
    log_info('mame_build_ROM_audit_databases() ROM set is {}'.format(rom_set))
    log_info('mame_build_ROM_audit_databases() CHD set is {}'.format(chd_set))

    # ---------------------------------------------------------------------------------------------
    # Audit database
    # ---------------------------------------------------------------------------------------------
    log_info('mame_build_ROM_audit_databases() Starting...')
    log_info('Building {} ROM/Sample audit database...'.format(rom_set_str))
    pDialog = KodiProgressDialog()
    pDialog.startProgress('Building {} ROM set...'.format(rom_set_str), len(machines))
    stats_audit_MAME_machines_runnable = 0
    audit_roms_dic = {}
    for m_name in sorted(machines):
        pDialog.updateProgressInc()

        # --- ROMs ---
        # Skip device machines.
        if renderdb_dic[m_name]['isDevice']: continue
        stats_audit_MAME_machines_runnable += 1
        m_roms = machine_roms[m_name]['roms']
        machine_rom_set = []
        for rom in m_roms:
            rom['type'] = _get_ROM_type(rom)
            rom['location'] = _get_ROM_location(rom_set, rom, m_name, machines, renderdb_dic, machine_roms)
            machine_rom_set.append(rom)

        # --- Device ROMs ---
        device_roms_list = []
        for device in devices_db_dic[m_name]:
            device_roms_dic = machine_roms[device]
            for rom in device_roms_dic['roms']:
                rom['type'] = ROM_TYPE_DROM
                rom['location'] = device + '/' + rom['name']
                device_roms_list.append(rom)
        if device_roms_list: machine_rom_set.extend(device_roms_list)

        # --- Samples ---
        sampleof = machines[m_name]['sampleof']
        m_samples = machine_roms[m_name]['samples']
        samples_list = []
        for sample in m_samples:
            sample['type'] = ROM_TYPE_SAMPLE
            sample['location'] = sampleof + '/' + sample['name']
            samples_list.append(sample)
        if samples_list: machine_rom_set.extend(samples_list)

        # Add ROMs to main DB
        audit_roms_dic[m_name] = machine_rom_set
    pDialog.endProgress()

    # --- CHD set (refactored code) ---------------------------------------------------------------
    log_info('Building {} CHD audit database...'.format(chd_set_str))
    pDialog.startProgress('Building {} CHD set...'.format(chd_set_str), len(machines))
    for m_name in sorted(machines):
        pDialog.updateProgressInc()
        # Skip Device Machines
        if renderdb_dic[m_name]['isDevice']: continue
        m_disks = machine_roms[m_name]['disks']
        machine_chd_set = []
        for disk in m_disks:
            disk['type'] = ROM_TYPE_DISK
            disk['location'] = _get_CHD_location(chd_set, disk, m_name, machines, renderdb_dic, machine_roms)
            machine_chd_set.append(disk)
        if m_name in audit_roms_dic:
            audit_roms_dic[m_name].extend(machine_chd_set)
        else:
            audit_roms_dic[m_name] = machine_chd_set
    pDialog.endProgress()

    # ---------------------------------------------------------------------------------------------
    # Machine files and ROM ZIP/Sample ZIP/CHD lists.
    # ---------------------------------------------------------------------------------------------
    # NOTE roms_dic and chds_dic may have invalid ROMs/CHDs. However, machine_archives_dic must
    #      have only valid ROM archives (ZIP/7Z).
    # For every machine, it goes ROM by ROM and makes a list of ZIP archive locations. Then, it
    # transforms the list into a set to have a list with unique elements.
    # roms_dic/chds_dic have invalid ROMs. Skip invalid ROMs.
    log_info('Building ROM ZIP/Sample ZIP/CHD file lists...')
    pDialog.startProgress('Building ROM, Sample and CHD archive lists...', len(machines))
    machine_archives_dic = {}
    full_ROM_archive_set = set()
    full_Sample_archive_set = set()
    full_CHD_archive_set = set()
    machine_archives_ROM = 0
    machine_archives_ROM_parents = 0
    machine_archives_ROM_clones = 0
    machine_archives_Samples = 0
    machine_archives_Samples_parents = 0
    machine_archives_Samples_clones = 0
    machine_archives_CHD = 0
    machine_archives_CHD_parents = 0
    machine_archives_CHD_clones = 0
    archive_less = 0
    archive_less_parents = 0
    archive_less_clones = 0
    ROMs_total = 0
    ROMs_valid = 0
    ROMs_invalid = 0
    CHDs_total = 0
    CHDs_valid = 0
    CHDs_invalid = 0
    for m_name in audit_roms_dic:
        pDialog.updateProgressInc()
        isClone = True if renderdb_dic[m_name]['cloneof'] else False
        rom_list = audit_roms_dic[m_name]
        machine_rom_archive_set = set()
        machine_sample_archive_set = set()
        machine_chd_archive_set = set()
        # --- Iterate ROMs/CHDs ---
        for rom in rom_list:
            if rom['type'] == ROM_TYPE_DISK:
                CHDs_total += 1
                # Skip invalid CHDs
                if not rom['sha1']:
                    CHDs_invalid += 1
                    continue
                CHDs_valid += 1
                chd_name = rom['location']
                machine_chd_archive_set.add(chd_name)
                full_CHD_archive_set.add(rom['location'])
            elif rom['type'] == ROM_TYPE_SAMPLE:
                sample_str_list = rom['location'].split('/')
                zip_name = sample_str_list[0]
                machine_sample_archive_set.add(zip_name)
                archive_str = rom['location'].split('/')[0]
                full_Sample_archive_set.add(archive_str)
            else:
                ROMs_total += 1
                # Skip invalid ROMs
                if not rom['crc']:
                    ROMs_invalid += 1
                    continue
                ROMs_valid += 1
                rom_str_list = rom['location'].split('/')
                zip_name = rom_str_list[0]
                machine_rom_archive_set.add(zip_name)
                archive_str = rom['location'].split('/')[0]
                # if not archive_str: continue
                full_ROM_archive_set.add(archive_str)
        machine_archives_dic[m_name] = {
            'ROMs'    : list(machine_rom_archive_set),
            'Samples' : list(machine_sample_archive_set),
            'CHDs'    : list(machine_chd_archive_set),
        }

        # --- Statistics ---
        if machine_rom_archive_set:
            machine_archives_ROM += 1
            if isClone:
                machine_archives_ROM_clones += 1
            else:
                machine_archives_ROM_parents += 1
        if machine_sample_archive_set:
            machine_archives_Samples += 1
            if isClone:
                machine_archives_Samples_clones += 1
            else:
                machine_archives_Samples_parents += 1
        if machine_chd_archive_set:
            machine_archives_CHD += 1
            if isClone:
                machine_archives_CHD_clones += 1
            else:
                machine_archives_CHD_parents += 1
        if not (machine_rom_archive_set or machine_sample_archive_set or machine_chd_archive_set):
            archive_less += 1
            if isClone:
                archive_less_clones += 1
            else:
                archive_less_parents += 1
    pDialog.endProgress()

    # ---------------------------------------------------------------------------------------------
    # machine_roms dictionary is passed as argument and not save in this function.
    # It is modified in this function to create audit_roms_dic.
    # Remove unused fields to save memory before saving the audit_roms_dic JSON file.
    # Do not remove earlier because 'merge' is used in the _get_XXX_location() functions.
    # ---------------------------------------------------------------------------------------------
    log_info('Cleaning audit database before saving it to disk...')
    pDialog.startProgress('Cleaning audit database...', len(machines))
    for m_name in sorted(machines):
        pDialog.updateProgressInc()
        # --- Skip devices and process ROMs and CHDs ---
        if renderdb_dic[m_name]['isDevice']: continue
        for rom in machine_roms[m_name]['roms']:
            # Remove unused fields to save space in JSON database, but remove from the copy!
            rom.pop('merge')
            rom.pop('bios')
        for disk in machine_roms[m_name]['disks']:
            disk.pop('merge')
    pDialog.endProgress()

    # ---------------------------------------------------------------------------------------------
    # Update control dictionary.
    # ---------------------------------------------------------------------------------------------
    db_safe_edit(control_dic, 'stats_audit_MAME_machines_runnable', stats_audit_MAME_machines_runnable)
    db_safe_edit(control_dic, 'stats_audit_MAME_ROM_ZIP_files', len(full_ROM_archive_set))
    db_safe_edit(control_dic, 'stats_audit_MAME_Sample_ZIP_files', len(full_Sample_archive_set))
    db_safe_edit(control_dic, 'stats_audit_MAME_CHD_files', len(full_CHD_archive_set))
    db_safe_edit(control_dic, 'stats_audit_machine_archives_ROM', machine_archives_ROM)
    db_safe_edit(control_dic, 'stats_audit_machine_archives_ROM_parents', machine_archives_ROM_parents)
    db_safe_edit(control_dic, 'stats_audit_machine_archives_ROM_clones', machine_archives_ROM_clones)
    db_safe_edit(control_dic, 'stats_audit_machine_archives_CHD', machine_archives_CHD)
    db_safe_edit(control_dic, 'stats_audit_machine_archives_CHD_parents', machine_archives_CHD_parents)
    db_safe_edit(control_dic, 'stats_audit_machine_archives_CHD_clones', machine_archives_CHD_clones)
    db_safe_edit(control_dic, 'stats_audit_machine_archives_Samples', machine_archives_Samples)
    db_safe_edit(control_dic, 'stats_audit_machine_archives_Samples_parents', machine_archives_Samples_parents)
    db_safe_edit(control_dic, 'stats_audit_machine_archives_Samples_clones', machine_archives_Samples_clones)
    db_safe_edit(control_dic, 'stats_audit_archive_less', archive_less)
    db_safe_edit(control_dic, 'stats_audit_archive_less_parents', archive_less_parents)
    db_safe_edit(control_dic, 'stats_audit_archive_less_clones', archive_less_clones)
    db_safe_edit(control_dic, 'stats_audit_ROMs_total', ROMs_total)
    db_safe_edit(control_dic, 'stats_audit_ROMs_valid', ROMs_valid)
    db_safe_edit(control_dic, 'stats_audit_ROMs_invalid', ROMs_invalid)
    db_safe_edit(control_dic, 'stats_audit_CHDs_total', CHDs_total)
    db_safe_edit(control_dic, 'stats_audit_CHDs_valid', CHDs_valid)
    db_safe_edit(control_dic, 'stats_audit_CHDs_invalid', CHDs_invalid)
    db_safe_edit(control_dic, 't_MAME_Audit_DB_build', time.time())

    # --- Save databases ---
    if OPTION_LOWMEM_WRITE_JSON:
        json_write_func = utils_write_JSON_file_lowmem
        log_debug('Using utils_write_JSON_file_lowmem() JSON writer')
    else:
        json_write_func = utils_write_JSON_file
        log_debug('Using utils_write_JSON_file() JSON writer')
    db_files = [
        [audit_roms_dic, 'MAME ROM Audit', cfg.ROM_AUDIT_DB_PATH.getPath()],
        [machine_archives_dic, 'Machine file list', cfg.ROM_SET_MACHINE_FILES_DB_PATH.getPath()],
        # --- Save control_dic after everything is saved ---
        [control_dic, 'Control dictionary', cfg.MAIN_CONTROL_PATH.getPath()],
    ]
    db_save_files(db_files, json_write_func)
    # Add data generated in this function to dictionary for caller code use.
    db_dic_in['audit_roms'] = audit_roms_dic
    db_dic_in['machine_archives'] = machine_archives_dic

#
# Checks for errors before scanning for SL ROMs.
# Display a Kodi dialog if an error is found.
# Returns a dictionary of settings:
# options_dic['abort'] is always present.
# 
#
def mame_check_before_build_MAME_catalogs(cfg, st_dic, control_dic):
    kodi_reset_status(st_dic)

    # --- Check that database exists ---
    pass

#
# Updates db_dic_in and adds cache_index field.
#
# A) Builds the following catalog files
#    CATALOG_MAIN_PARENT_PATH
#    CATALOG_MAIN_ALL_PATH
#    CATALOG_CATVER_PARENT_PATH
#    CATALOG_CATVER_ALL_PATH
#    ...
#
#    main_catalog_parents = {
#        'cat_key' : [ parent1, parent2, ... ]
#    }
#
#    main_catalog_all = {
#        'cat_key' : [ machine1, machine2, ... ]
#    }
#
# B) Cache index:
#    CACHE_INDEX_PATH
#
#    cache_index_dic = {
#        'catalog_name' : { --> 'Main', 'Binary', ...
#            'cat_key' : {
#                'num_machines' : int,
#                'num_parents' : int,
#                'hash' : text_type
#            }, ...
#        }, ...
#    }
#
def mame_build_MAME_catalogs(cfg, st_dic, db_dic_in):
    control_dic = db_dic_in['control_dic']
    machines = db_dic_in['machines']
    renderdb_dic = db_dic_in['renderdb']
    assetdb_dic = db_dic_in['assetdb']
    machine_roms = db_dic_in['roms']
    main_pclone_dic = db_dic_in['main_pclone_dic']

    # --- Machine count ---
    cache_index_dic = {
        # Virtual Main filter catalog
        'Main'               : {},
        # Virtual Binary filter catalog
        'Binary'             : {},
        # INI/DAT based catalogs
        'Catver'             : {},
        'Catlist'            : {},
        'Genre'              : {},
        'Category'           : {},
        'NPlayers'           : {},
        'Bestgames'          : {},
        'Series'             : {},
        'Alltime'            : {},
        'Artwork'            : {},
        'Version'            : {},
        # MAME XML extracted catalogs
        'Controls_Expanded'  : {},
        'Controls_Compact'   : {},
        'Devices_Expanded'   : {},
        'Devices_Compact'    : {},
        'Display_Type'       : {},
        'Display_VSync'      : {},
        'Display_Resolution' : {},
        'CPU'                : {},
        'Driver'             : {},
        'Manufacturer'       : {},
        'ShortName'          : {},
        'LongName'           : {},
        'BySL'               : {},
        'Year'               : {},
    }
    NUM_CATALOGS = len(cache_index_dic)

    NORMAL_DRIVER_SET = {
        '88games.cpp',
        'asteroid.cpp',
        'cball.cpp',
    }
    UNUSUAL_DRIVER_SET = {
        'aristmk5.cpp',
        'adp.cpp',
        'cubo.cpp',
        'mpu4vid.cpp',
        'peplus.cpp',
        'sfbonus.cpp',
    }

    # --- Progress dialog ---
    diag_line1 = 'Building catalogs...'
    pDialog = KodiProgressDialog()
    processed_filters = 0

    # ---------------------------------------------------------------------------------------------
    # Main filters (None catalog) -----------------------------------------------------------------
    # ---------------------------------------------------------------------------------------------
    pDialog.startProgress('{}\n{}'.format(diag_line1, 'Main catalog'), NUM_CATALOGS)
    main_catalog_parents, main_catalog_all = {}, {}

    # --- Normal and Unusual machine list ---
    # Machines with Coin Slot and Non Mechanical and not Dead and not Device
    log_info('Making None catalog - Coin index ...')
    normal_parent_dic, normal_all_dic, unusual_parent_dic, unusual_all_dic = {}, {}, {}, {}
    for parent_name in main_pclone_dic:
        machine_main = machines[parent_name]
        machine_render = renderdb_dic[parent_name]
        n_coins = machine_main['input']['att_coins'] if machine_main['input'] else 0
        if machine_main['isMechanical']: continue
        if n_coins == 0: continue
        if machine_main['isDead']: continue
        if machine_render['isDevice']: continue

        # Make list of machine controls.
        if machine_main['input']:
            control_list = [ctrl_dic['type'] for ctrl_dic in machine_main['input']['control_list']]
        else:
            control_list = []

        # --- Determinte if machine is Normal or Unusual ----
        # Standard machines.
        if ('only_buttons' in control_list and len(control_list) > 1) \
            or machine_main['sourcefile'] in NORMAL_DRIVER_SET:
            normal_parent_dic[parent_name] = machine_render['description']
            normal_all_dic[parent_name] = machine_render['description']
            mame_catalog_add_clones(parent_name, main_pclone_dic, renderdb_dic, normal_all_dic)
        #
        # Unusual machines. Most of them you don't wanna play.
        # No controls or control_type has "only_buttons" or "gambling" or "hanafuda" or "mahjong"
        #
        elif not control_list \
            or 'only_buttons' in control_list or 'gambling' in control_list \
            or 'hanafuda' in control_list or 'mahjong' in control_list \
            or machine_main['sourcefile'] in UNUSUAL_DRIVER_SET:
            unusual_parent_dic[parent_name] = machine_render['description']
            unusual_all_dic[parent_name] = machine_render['description']
            mame_catalog_add_clones(parent_name, main_pclone_dic, renderdb_dic, unusual_all_dic)
        #
        # What remains go to the Normal/Standard list.
        #
        else:
            normal_parent_dic[parent_name] = machine_render['description']
            normal_all_dic[parent_name] = machine_render['description']
            mame_catalog_add_clones(parent_name, main_pclone_dic, renderdb_dic, normal_all_dic)
    main_catalog_parents['Normal'] = normal_parent_dic
    main_catalog_all['Normal'] = normal_all_dic
    main_catalog_parents['Unusual'] = unusual_parent_dic
    main_catalog_all['Unusual'] = unusual_all_dic

    # --- NoCoin list ---
    # A) Machines with No Coin Slot and Non Mechanical and not Dead and not Device
    log_info('Making NoCoin index ...')
    parent_dic, all_dic = {}, {}
    for parent_name in main_pclone_dic:
        machine_main = machines[parent_name]
        machine_render = renderdb_dic[parent_name]
        n_coins = machine_main['input']['att_coins'] if machine_main['input'] else 0
        if machine_main['isMechanical']: continue
        if n_coins > 0: continue
        if machine_main['isDead']: continue
        if machine_render['isDevice']: continue
        parent_dic[parent_name] = machine_render['description']
        all_dic[parent_name] = machine_render['description']
        mame_catalog_add_clones(parent_name, main_pclone_dic, renderdb_dic, all_dic)
    main_catalog_parents['NoCoin'] = parent_dic
    main_catalog_all['NoCoin'] = all_dic

    # --- Mechanical machines ---
    # Mechanical machines and not Dead and not Device
    log_info('Making Mechanical index ...')
    parent_dic, all_dic = {}, {}
    for parent_name in main_pclone_dic:
        machine_main = machines[parent_name]
        machine_render = renderdb_dic[parent_name]
        if not machine_main['isMechanical']: continue
        if machine_main['isDead']: continue
        if machine_render['isDevice']: continue
        parent_dic[parent_name] = machine_render['description']
        all_dic[parent_name] = machine_render['description']
        mame_catalog_add_clones(parent_name, main_pclone_dic, renderdb_dic, all_dic)
    main_catalog_parents['Mechanical'] = parent_dic
    main_catalog_all['Mechanical'] = all_dic

    # --- Dead machines ---
    log_info('Making Dead Machines index ...')
    parent_dic, all_dic = {}, {}
    for parent_name in main_pclone_dic:
        machine_main = machines[parent_name]
        machine_render = renderdb_dic[parent_name]
        if not machine_main['isDead']: continue
        parent_dic[parent_name] = machine_render['description']
        all_dic[parent_name] = machine_render['description']
        mame_catalog_add_clones(parent_name, main_pclone_dic, renderdb_dic, all_dic)
    main_catalog_parents['Dead'] = parent_dic
    main_catalog_all['Dead'] = all_dic

    # --- Device machines ---
    log_info('Making Device Machines index ...')
    parent_dic, all_dic = {}, {}
    for parent_name in main_pclone_dic:
        machine_render = renderdb_dic[parent_name]
        if not machine_render['isDevice']: continue
        parent_dic[parent_name] = machine_render['description']
        all_dic[parent_name] = machine_render['description']
        mame_catalog_add_clones(parent_name, main_pclone_dic, renderdb_dic, all_dic)
    main_catalog_parents['Devices'] = parent_dic
    main_catalog_all['Devices'] = all_dic

    # --- Build ROM cache index and save Main catalog JSON file ---
    mame_cache_index_builder('Main', cache_index_dic, main_catalog_all, main_catalog_parents)
    utils_write_JSON_file(cfg.CATALOG_MAIN_ALL_PATH.getPath(), main_catalog_all)
    utils_write_JSON_file(cfg.CATALOG_MAIN_PARENT_PATH.getPath(), main_catalog_parents)
    processed_filters += 1

    # ---------------------------------------------------------------------------------------------
    # Binary filters ------------------------------------------------------------------------------
    # ---------------------------------------------------------------------------------------------
    pDialog.updateProgress(processed_filters, '{}\n{}'.format(diag_line1, 'Binary catalog'))
    binary_catalog_parents, binary_catalog_all = {}, {}

    # --- CHD machines ---
    log_info('Making CHD Machines index ...')
    parent_dic, all_dic = {}, {}
    for parent_name in main_pclone_dic:
        machine = machines[parent_name]
        machine_render = renderdb_dic[parent_name]
        if machine_render['isDevice']: continue # >> Skip device machines
        if not machine_roms[parent_name]['disks']: continue
        parent_dic[parent_name] = machine_render['description']
        all_dic[parent_name] = machine_render['description']
        mame_catalog_add_clones(parent_name, main_pclone_dic, renderdb_dic, all_dic)
    binary_catalog_parents['CHD'] = parent_dic
    binary_catalog_all['CHD'] = all_dic

    # --- Machines with samples ---
    log_info('Making Samples Machines index ...')
    parent_dic, all_dic = {}, {}
    for parent_name in main_pclone_dic:
        machine = machines[parent_name]
        machine_render = renderdb_dic[parent_name]
        if machine_render['isDevice']: continue # >> Skip device machines
        if not machine['sampleof']: continue
        parent_dic[parent_name] = machine_render['description']
        all_dic[parent_name] = machine_render['description']
        mame_catalog_add_clones(parent_name, main_pclone_dic, renderdb_dic, all_dic)
    binary_catalog_parents['Samples'] = parent_dic
    binary_catalog_all['Samples'] = all_dic

    # --- Software List machines ---
    log_info('Making Software List Machines index ...')
    parent_dic, all_dic = {}, {}
    for parent_name in main_pclone_dic:
        machine = machines[parent_name]
        machine_render = renderdb_dic[parent_name]
        if machine_render['isDevice']: continue # >> Skip device machines
        if not machine['softwarelists']: continue
        parent_dic[parent_name] = machine_render['description']
        all_dic[parent_name] = machine_render['description']
        mame_catalog_add_clones(parent_name, main_pclone_dic, renderdb_dic, all_dic)
    binary_catalog_parents['SoftwareLists'] = parent_dic
    binary_catalog_all['SoftwareLists'] = all_dic

    # --- BIOS ---
    log_info('Making BIOS Machines index ...')
    parent_dic, all_dic = {}, {}
    for parent_name in main_pclone_dic:
        machine_render = renderdb_dic[parent_name]
        if machine_render['isDevice']: continue # Skip device machines
        if not machine_render['isBIOS']: continue
        parent_dic[parent_name] = machine_render['description']
        all_dic[parent_name] = machine_render['description']
        mame_catalog_add_clones(parent_name, main_pclone_dic, renderdb_dic, all_dic)
    binary_catalog_parents['BIOS'] = parent_dic
    binary_catalog_all['BIOS'] = all_dic

    # Build cache index and save Binary catalog JSON file
    mame_cache_index_builder('Binary', cache_index_dic, binary_catalog_all, binary_catalog_parents)
    utils_write_JSON_file(cfg.CATALOG_BINARY_ALL_PATH.getPath(), binary_catalog_all)
    utils_write_JSON_file(cfg.CATALOG_BINARY_PARENT_PATH.getPath(), binary_catalog_parents)
    processed_filters += 1

    # ---------------------------------------------------------------------------------------------
    # Cataloged machine lists ---------------------------------------------------------------------
    # ---------------------------------------------------------------------------------------------
    # --- Catver catalog ---
    pDialog.updateProgress(processed_filters, '{}\n{}'.format(diag_line1, 'Catver catalog'))
    log_info('Making Catver catalog ...')
    catalog_parents, catalog_all = {}, {}
    mame_build_catalog_helper(catalog_parents, catalog_all,
        machines, renderdb_dic, main_pclone_dic, mame_catalog_key_Catver)
    mame_cache_index_builder('Catver', cache_index_dic, catalog_all, catalog_parents)
    utils_write_JSON_file(cfg.CATALOG_CATVER_PARENT_PATH.getPath(), catalog_parents)
    utils_write_JSON_file(cfg.CATALOG_CATVER_ALL_PATH.getPath(), catalog_all)
    processed_filters += 1

    # --- Catlist catalog ---
    pDialog.updateProgress(processed_filters, '{}\n{}'.format(diag_line1, 'Catlist catalog'))
    log_info('Making Catlist catalog ...')
    catalog_parents, catalog_all = {}, {}
    mame_build_catalog_helper(catalog_parents, catalog_all,
        machines, renderdb_dic, main_pclone_dic, mame_catalog_key_Catlist)
    mame_cache_index_builder('Catlist', cache_index_dic, catalog_all, catalog_parents)
    utils_write_JSON_file(cfg.CATALOG_CATLIST_PARENT_PATH.getPath(), catalog_parents)
    utils_write_JSON_file(cfg.CATALOG_CATLIST_ALL_PATH.getPath(), catalog_all)
    processed_filters += 1

    # --- Genre catalog ---
    pDialog.updateProgress(processed_filters, '{}\n{}'.format(diag_line1, 'Genre catalog'))
    log_info('Making Genre catalog ...')
    catalog_parents, catalog_all = {}, {}
    mame_build_catalog_helper(catalog_parents, catalog_all,
        machines, renderdb_dic, main_pclone_dic, mame_catalog_key_Genre)
    mame_cache_index_builder('Genre', cache_index_dic, catalog_all, catalog_parents)
    utils_write_JSON_file(cfg.CATALOG_GENRE_PARENT_PATH.getPath(), catalog_parents)
    utils_write_JSON_file(cfg.CATALOG_GENRE_ALL_PATH.getPath(), catalog_all)
    processed_filters += 1

    # --- Category catalog ---
    pDialog.updateProgress(processed_filters, '{}\n{}'.format(diag_line1, 'Category catalog'))
    log_info('Making Category catalog ...')
    catalog_parents, catalog_all = {}, {}
    mame_build_catalog_helper(catalog_parents, catalog_all,
        machines, renderdb_dic, main_pclone_dic, mame_catalog_key_Category)
    mame_cache_index_builder('Category', cache_index_dic, catalog_all, catalog_parents)
    utils_write_JSON_file(cfg.CATALOG_CATEGORY_PARENT_PATH.getPath(), catalog_parents)
    utils_write_JSON_file(cfg.CATALOG_CATEGORY_ALL_PATH.getPath(), catalog_all)
    processed_filters += 1

    # --- Nplayers catalog ---
    pDialog.updateProgress(processed_filters, '{}\n{}'.format(diag_line1, 'Nplayers catalog'))
    log_info('Making Nplayers catalog ...')
    catalog_parents, catalog_all = {}, {}
    mame_build_catalog_helper(catalog_parents, catalog_all,
        renderdb_dic, renderdb_dic, main_pclone_dic, mame_catalog_key_NPlayers)
    mame_cache_index_builder('NPlayers', cache_index_dic, catalog_all, catalog_parents)
    utils_write_JSON_file(cfg.CATALOG_NPLAYERS_PARENT_PATH.getPath(), catalog_parents)
    utils_write_JSON_file(cfg.CATALOG_NPLAYERS_ALL_PATH.getPath(), catalog_all)
    processed_filters += 1

    # --- Bestgames catalog ---
    pDialog.updateProgress(processed_filters, '{}\n{}'.format(diag_line1, 'Bestgames catalog'))
    log_info('Making Bestgames catalog ...')
    catalog_parents, catalog_all = {}, {}
    mame_build_catalog_helper(catalog_parents, catalog_all,
        machines, renderdb_dic, main_pclone_dic, mame_catalog_key_Bestgames)
    mame_cache_index_builder('Bestgames', cache_index_dic, catalog_all, catalog_parents)
    utils_write_JSON_file(cfg.CATALOG_BESTGAMES_PARENT_PATH.getPath(), catalog_parents)
    utils_write_JSON_file(cfg.CATALOG_BESTGAMES_ALL_PATH.getPath(), catalog_all)
    processed_filters += 1

    # --- Series catalog ---
    pDialog.updateProgress(processed_filters, '{}\n{}'.format(diag_line1, 'Series catalog'))
    log_info('Making Series catalog ...')
    catalog_parents, catalog_all = {}, {}
    mame_build_catalog_helper(catalog_parents, catalog_all,
        machines, renderdb_dic, main_pclone_dic, mame_catalog_key_Series)
    mame_cache_index_builder('Series', cache_index_dic, catalog_all, catalog_parents)
    utils_write_JSON_file(cfg.CATALOG_SERIES_PARENT_PATH.getPath(), catalog_parents)
    utils_write_JSON_file(cfg.CATALOG_SERIES_ALL_PATH.getPath(), catalog_all)
    processed_filters += 1

    # --- Alltime catalog ---
    pDialog.updateProgress(processed_filters, '{}\n{}'.format(diag_line1, 'Alltime catalog'))
    log_info('Making Alltime catalog ...')
    catalog_parents, catalog_all = {}, {}
    mame_build_catalog_helper(catalog_parents, catalog_all,
        machines, renderdb_dic, main_pclone_dic, mame_catalog_key_Alltime)
    mame_cache_index_builder('Alltime', cache_index_dic, catalog_all, catalog_parents)
    utils_write_JSON_file(cfg.CATALOG_ALLTIME_PARENT_PATH.getPath(), catalog_parents)
    utils_write_JSON_file(cfg.CATALOG_ALLTIME_ALL_PATH.getPath(), catalog_all)
    processed_filters += 1

    # --- Artwork catalog ---
    pDialog.updateProgress(processed_filters, '{}\n{}'.format(diag_line1, 'Artwork catalog'))
    log_info('Making Artwork catalog ...')
    catalog_parents, catalog_all = {}, {}
    mame_build_catalog_helper(catalog_parents, catalog_all,
        machines, renderdb_dic, main_pclone_dic, mame_catalog_key_Artwork)
    mame_cache_index_builder('Artwork', cache_index_dic, catalog_all, catalog_parents)
    utils_write_JSON_file(cfg.CATALOG_ARTWORK_PARENT_PATH.getPath(), catalog_parents)
    utils_write_JSON_file(cfg.CATALOG_ARTWORK_ALL_PATH.getPath(), catalog_all)
    processed_filters += 1

    # --- Version catalog ---
    pDialog.updateProgress(processed_filters, '{}\n{}'.format(diag_line1, 'Version catalog'))
    log_info('Making Version catalog ...')
    catalog_parents, catalog_all = {}, {}
    mame_build_catalog_helper(catalog_parents, catalog_all,
        machines, renderdb_dic, main_pclone_dic, mame_catalog_key_VerAdded)
    mame_cache_index_builder('Version', cache_index_dic, catalog_all, catalog_parents)
    utils_write_JSON_file(cfg.CATALOG_VERADDED_PARENT_PATH.getPath(), catalog_parents)
    utils_write_JSON_file(cfg.CATALOG_VERADDED_ALL_PATH.getPath(), catalog_all)
    processed_filters += 1

    # --- Control catalog (Expanded) ---
    pDialog.updateProgress(processed_filters, '{}\n{}'.format(diag_line1, 'Control Expanded catalog'))
    log_info('Making Control Expanded catalog ...')
    catalog_parents, catalog_all = {}, {}
    mame_build_catalog_helper(catalog_parents, catalog_all,
        machines, renderdb_dic, main_pclone_dic, mame_catalog_key_Controls_Expanded)
    mame_cache_index_builder('Controls_Expanded', cache_index_dic, catalog_all, catalog_parents)
    utils_write_JSON_file(cfg.CATALOG_CONTROL_EXPANDED_PARENT_PATH.getPath(), catalog_parents)
    utils_write_JSON_file(cfg.CATALOG_CONTROL_EXPANDED_ALL_PATH.getPath(), catalog_all)
    processed_filters += 1

    # --- Control catalog (Compact) ---
    # In this catalog one machine may be in several categories if the machine has more than
    # one control.
    pDialog.updateProgress(processed_filters, '{}\n{}'.format(diag_line1, 'Control Compact catalog'))
    log_info('Making Control Compact catalog ...')
    catalog_parents, catalog_all = {}, {}
    mame_build_catalog_helper(catalog_parents, catalog_all,
        machines, renderdb_dic, main_pclone_dic, mame_catalog_key_Controls_Compact)
    mame_cache_index_builder('Controls_Compact', cache_index_dic, catalog_all, catalog_parents)
    utils_write_JSON_file(cfg.CATALOG_CONTROL_COMPACT_PARENT_PATH.getPath(), catalog_parents)
    utils_write_JSON_file(cfg.CATALOG_CONTROL_COMPACT_ALL_PATH.getPath(), catalog_all)
    processed_filters += 1

    # --- <device> / Device Expanded catalog ---
    pDialog.updateProgress(processed_filters, '{}\n{}'.format(diag_line1, '<device> Expanded catalog'))
    log_info('Making <device> tag Expanded catalog ...')
    catalog_parents, catalog_all = {}, {}
    mame_build_catalog_helper(catalog_parents, catalog_all,
        machines, renderdb_dic, main_pclone_dic, mame_catalog_key_Devices_Expanded)
    mame_cache_index_builder('Devices_Expanded', cache_index_dic, catalog_all, catalog_parents)
    utils_write_JSON_file(cfg.CATALOG_DEVICE_EXPANDED_PARENT_PATH.getPath(), catalog_parents)
    utils_write_JSON_file(cfg.CATALOG_DEVICE_EXPANDED_ALL_PATH.getPath(), catalog_all)
    processed_filters += 1

    # --- <device> / Device Compact catalog ---
    pDialog.updateProgress(processed_filters, '{}\n{}'.format(diag_line1, '<device> Compact catalog'))
    log_info('Making <device> tag Compact catalog ...')
    catalog_parents, catalog_all = {}, {}
    mame_build_catalog_helper(catalog_parents, catalog_all,
        machines, renderdb_dic, main_pclone_dic, mame_catalog_key_Devices_Compact)
    mame_cache_index_builder('Devices_Compact', cache_index_dic, catalog_all, catalog_parents)
    utils_write_JSON_file(cfg.CATALOG_DEVICE_COMPACT_PARENT_PATH.getPath(), catalog_parents)
    utils_write_JSON_file(cfg.CATALOG_DEVICE_COMPACT_ALL_PATH.getPath(), catalog_all)
    processed_filters += 1

    # --- Display Type catalog ---
    pDialog.updateProgress(processed_filters, '{}\n{}'.format(diag_line1, 'Display Type catalog'))
    log_info('Making Display Type catalog ...')
    catalog_parents, catalog_all = {}, {}
    mame_build_catalog_helper(catalog_parents, catalog_all,
        machines, renderdb_dic, main_pclone_dic, mame_catalog_key_Display_Type)
    mame_cache_index_builder('Display_Type', cache_index_dic, catalog_all, catalog_parents)
    utils_write_JSON_file(cfg.CATALOG_DISPLAY_TYPE_PARENT_PATH.getPath(), catalog_parents)
    utils_write_JSON_file(cfg.CATALOG_DISPLAY_TYPE_ALL_PATH.getPath(), catalog_all)
    processed_filters += 1

    # --- Display VSync catalog ---
    pDialog.updateProgress(processed_filters, '{}\n{}'.format(diag_line1, 'Display VSync catalog'))
    log_info('Making Display VSync catalog ...')
    catalog_parents, catalog_all = {}, {}
    mame_build_catalog_helper(catalog_parents, catalog_all,
        machines, renderdb_dic, main_pclone_dic, mame_catalog_key_Display_VSync)
    mame_cache_index_builder('Display_VSync', cache_index_dic, catalog_all, catalog_parents)
    utils_write_JSON_file(cfg.CATALOG_DISPLAY_VSYNC_PARENT_PATH.getPath(), catalog_parents)
    utils_write_JSON_file(cfg.CATALOG_DISPLAY_VSYNC_ALL_PATH.getPath(), catalog_all)
    processed_filters += 1

    # --- Display Resolution catalog ---
    pDialog.updateProgress(processed_filters, '{}\n{}'.format(diag_line1, 'Display Resolution catalog'))
    log_info('Making Display Resolution catalog ...')
    catalog_parents, catalog_all = {}, {}
    mame_build_catalog_helper(catalog_parents, catalog_all,
        machines, renderdb_dic, main_pclone_dic, mame_catalog_key_Display_Resolution)
    mame_cache_index_builder('Display_Resolution', cache_index_dic, catalog_all, catalog_parents)
    utils_write_JSON_file(cfg.CATALOG_DISPLAY_RES_PARENT_PATH.getPath(), catalog_parents)
    utils_write_JSON_file(cfg.CATALOG_DISPLAY_RES_ALL_PATH.getPath(), catalog_all)
    processed_filters += 1

    # --- CPU catalog ---
    pDialog.updateProgress(processed_filters, '{}\n{}'.format(diag_line1, 'CPU catalog'))
    log_info('Making CPU catalog ...')
    catalog_parents, catalog_all = {}, {}
    mame_build_catalog_helper(catalog_parents, catalog_all,
        machines, renderdb_dic, main_pclone_dic, mame_catalog_key_CPU)
    mame_cache_index_builder('CPU', cache_index_dic, catalog_all, catalog_parents)
    utils_write_JSON_file(cfg.CATALOG_CPU_PARENT_PATH.getPath(), catalog_parents)
    utils_write_JSON_file(cfg.CATALOG_CPU_ALL_PATH.getPath(), catalog_all)
    processed_filters += 1

    # --- Driver catalog ---
    # This catalog cannot use mame_build_catalog_helper() because of the driver
    # name substitution.
    pDialog.updateProgress(processed_filters, '{}\n{}'.format(diag_line1, 'Driver catalog'))
    log_info('Making Driver catalog ...')
    catalog_parents, catalog_all = {}, {}
    # mame_build_catalog_helper(catalog_parents, catalog_all,
    #     machines, renderdb_dic, main_pclone_dic, mame_catalog_key_Driver)
    for parent_name in main_pclone_dic:
        render = renderdb_dic[parent_name]
        if render['isDevice']: continue # Skip device machines in catalogs.
        c_key = machines[parent_name]['sourcefile']
        # Some drivers get a prettier name.
        c_key = mame_driver_better_name_dic[c_key] if c_key in mame_driver_better_name_dic else c_key
        catalog_key_list = [c_key]
        for catalog_key in catalog_key_list:
            if catalog_key in catalog_parents:
                catalog_parents[catalog_key][parent_name] = render['description']
                catalog_all[catalog_key][parent_name] = render['description']
            else:
                catalog_parents[catalog_key] = { parent_name : render['description'] }
                catalog_all[catalog_key] = { parent_name : render['description'] }
            for clone_name in main_pclone_dic[parent_name]:
                catalog_all[catalog_key][clone_name] = renderdb_dic[clone_name]['description']
    mame_cache_index_builder('Driver', cache_index_dic, catalog_all, catalog_parents)
    utils_write_JSON_file(cfg.CATALOG_DRIVER_PARENT_PATH.getPath(), catalog_parents)
    utils_write_JSON_file(cfg.CATALOG_DRIVER_ALL_PATH.getPath(), catalog_all)
    processed_filters += 1

    # --- Manufacturer catalog ---
    pDialog.updateProgress(processed_filters, '{}\n{}'.format(diag_line1, 'Manufacturer catalog'))
    log_info('Making Manufacturer catalog ...')
    catalog_parents, catalog_all = {}, {}
    mame_build_catalog_helper(catalog_parents, catalog_all,
        machines, renderdb_dic, main_pclone_dic, mame_catalog_key_Manufacturer)
    mame_cache_index_builder('Manufacturer', cache_index_dic, catalog_all, catalog_parents)
    utils_write_JSON_file(cfg.CATALOG_MANUFACTURER_PARENT_PATH.getPath(), catalog_parents)
    utils_write_JSON_file(cfg.CATALOG_MANUFACTURER_ALL_PATH.getPath(), catalog_all)
    processed_filters += 1

    # --- MAME short name catalog ---
    # This catalog cannot use mame_build_catalog_helper() because of the special name
    # of the catalog (it is not the plain description).
    pDialog.updateProgress(processed_filters, '{}\n{}'.format(diag_line1, 'Short name catalog'))
    log_info('Making MAME short name catalog...')
    catalog_parents, catalog_all = {}, {}
    for parent_name in main_pclone_dic:
        render = renderdb_dic[parent_name]
        if render['isDevice']: continue
        catalog_key = parent_name[0]
        t = '{} "{}"'.format(parent_name, render['description'])
        if catalog_key in catalog_parents:
            catalog_parents[catalog_key][parent_name] = t
            catalog_all[catalog_key][parent_name] = t
        else:
            catalog_parents[catalog_key] = { parent_name : t }
            catalog_all[catalog_key] = { parent_name : t }
        for clone_name in main_pclone_dic[parent_name]:
            t = '{} "{}"'.format(clone_name, renderdb_dic[clone_name]['description'])
            catalog_all[catalog_key][clone_name] = t
    mame_cache_index_builder('ShortName', cache_index_dic, catalog_all, catalog_parents)
    utils_write_JSON_file(cfg.CATALOG_SHORTNAME_PARENT_PATH.getPath(), catalog_parents)
    utils_write_JSON_file(cfg.CATALOG_SHORTNAME_ALL_PATH.getPath(), catalog_all)
    processed_filters += 1

    # --- MAME long name catalog ---
    pDialog.updateProgress(processed_filters, '{}\n{}'.format(diag_line1, 'Long name catalog'))
    log_info('Making MAME long name catalog ...')
    catalog_parents, catalog_all = {}, {}
    mame_build_catalog_helper(catalog_parents, catalog_all,
        machines, renderdb_dic, main_pclone_dic, mame_catalog_key_LongName)
    mame_cache_index_builder('LongName', cache_index_dic, catalog_all, catalog_parents)
    utils_write_JSON_file(cfg.CATALOG_LONGNAME_PARENT_PATH.getPath(), catalog_parents)
    utils_write_JSON_file(cfg.CATALOG_LONGNAME_ALL_PATH.getPath(), catalog_all)
    processed_filters += 1

    # --- Software List (BySL) catalog ---
    # This catalog cannot use mame_build_catalog_helper() because of the name change of the SLs.
    pDialog.updateProgress(processed_filters, '{}\n{}'.format(diag_line1, 'Software List catalog'))
    log_info('Making Software List catalog ...')
    # Load proper Software List proper names, if available
    SL_names_dic = utils_load_JSON_file(cfg.SL_NAMES_PATH.getPath())
    catalog_parents, catalog_all = {}, {}
    for parent_name in main_pclone_dic:
        machine = machines[parent_name]
        render = renderdb_dic[parent_name]
        if render['isDevice']: continue
        for sl_name in machine['softwarelists']:
            catalog_key = sl_name
            if catalog_key in SL_names_dic: catalog_key = SL_names_dic[catalog_key]
            if catalog_key in catalog_parents:
                catalog_parents[catalog_key][parent_name] = render['description']
                catalog_all[catalog_key][parent_name] = render['description']
            else:
                catalog_parents[catalog_key] = { parent_name : render['description'] }
                catalog_all[catalog_key] = { parent_name : render['description'] }
            mame_catalog_add_clones(parent_name, main_pclone_dic, renderdb_dic, catalog_all[catalog_key])
    # Add orphaned Software Lists (SL that do not have an associated machine).
    for sl_name in SL_names_dic:
        catalog_key = sl_name
        if catalog_key in SL_names_dic: catalog_key = SL_names_dic[catalog_key]
        if catalog_key in catalog_parents: continue
        catalog_parents[catalog_key] = {}
        catalog_all[catalog_key] = {}
    mame_cache_index_builder('BySL', cache_index_dic, catalog_all, catalog_parents)
    utils_write_JSON_file(cfg.CATALOG_SL_PARENT_PATH.getPath(), catalog_parents)
    utils_write_JSON_file(cfg.CATALOG_SL_ALL_PATH.getPath(), catalog_all)
    processed_filters += 1

    # --- Year catalog ---
    pDialog.updateProgress(processed_filters, '{}\n{}'.format(diag_line1, 'Year catalog'))
    log_info('Making Year catalog ...')
    catalog_parents, catalog_all = {}, {}
    mame_build_catalog_helper(catalog_parents, catalog_all,
        machines, renderdb_dic, main_pclone_dic, mame_catalog_key_Year)
    mame_cache_index_builder('Year', cache_index_dic, catalog_all, catalog_parents)
    utils_write_JSON_file(cfg.CATALOG_YEAR_PARENT_PATH.getPath(), catalog_parents)
    utils_write_JSON_file(cfg.CATALOG_YEAR_ALL_PATH.getPath(), catalog_all)
    processed_filters += 1

    # Close progress dialog.
    pDialog.endProgress()

    # --- Create properties database with default values ------------------------------------------
    # Now overwrites all properties when the catalog is rebuilt.
    # New versions must kept user set properties!
    # This code is disabled
    # mame_properties_dic = {}
    # for catalog_name in CATALOG_NAME_LIST:
    #     catalog_dic = db_get_cataloged_dic_parents(cfg, catalog_name)
    #     for category_name in sorted(catalog_dic):
    #         prop_key = '{} - {}'.format(catalog_name, category_name)
    #         mame_properties_dic[prop_key] = {'vm' : VIEW_MODE_PCLONE}
    # utils_write_JSON_file(cfg.MAIN_PROPERTIES_PATH.getPath(), mame_properties_dic)
    # log_info('mame_properties_dic has {} entries'.format(len(mame_properties_dic)))

    # --- Compute main filter statistics ---
    stats_MF_Normal_Total, stats_MF_Normal_Total_parents = 0, 0
    stats_MF_Normal_Good, stats_MF_Normal_Good_parents = 0, 0
    stats_MF_Normal_Imperfect, stats_MF_Normal_Imperfect_parents = 0, 0
    stats_MF_Normal_Nonworking, stats_MF_Normal_Nonworking_parents = 0, 0
    stats_MF_Unusual_Total, stats_MF_Unusual_Total_parents = 0, 0
    stats_MF_Unusual_Good, stats_MF_Unusual_Good_parents = 0, 0
    stats_MF_Unusual_Imperfect, stats_MF_Unusual_Imperfect_parents = 0, 0
    stats_MF_Unusual_Nonworking, stats_MF_Unusual_Nonworking_parents = 0, 0
    stats_MF_Nocoin_Total, stats_MF_Nocoin_Total_parents = 0, 0
    stats_MF_Nocoin_Good, stats_MF_Nocoin_Good_parents = 0, 0
    stats_MF_Nocoin_Imperfect, stats_MF_Nocoin_Imperfect_parents = 0, 0
    stats_MF_Nocoin_Nonworking, stats_MF_Nocoin_Nonworking_parents = 0, 0
    stats_MF_Mechanical_Total, stats_MF_Mechanical_Total_parents = 0, 0
    stats_MF_Mechanical_Good, stats_MF_Mechanical_Good_parents = 0, 0
    stats_MF_Mechanical_Imperfect, stats_MF_Mechanical_Imperfect_parents = 0, 0
    stats_MF_Mechanical_Nonworking, stats_MF_Mechanical_Nonworking_parents = 0, 0
    stats_MF_Dead_Total, stats_MF_Dead_Total_parents = 0, 0
    stats_MF_Dead_Good, stats_MF_Dead_Good_parents = 0, 0
    stats_MF_Dead_Imperfect, stats_MF_Dead_Imperfect_parents = 0, 0
    stats_MF_Dead_Nonworking, stats_MF_Dead_Nonworking_parents = 0, 0
    NUM_FILTERS = 5
    processed_filters = 0
    pDialog.startProgress('Computing statistics ...', NUM_FILTERS)
    for m_name in main_catalog_all['Normal']:
        driver_status = renderdb_dic[m_name]['driver_status']
        stats_MF_Normal_Total += 1
        if not renderdb_dic[m_name]['cloneof']: stats_MF_Normal_Total_parents += 1
        if driver_status == 'good':
            stats_MF_Normal_Good += 1
            if not renderdb_dic[m_name]['cloneof']: stats_MF_Normal_Good_parents += 1
        elif driver_status == 'imperfect':
            stats_MF_Normal_Imperfect += 1
            if not renderdb_dic[m_name]['cloneof']: stats_MF_Normal_Imperfect_parents += 1
        elif driver_status == 'preliminary':
            stats_MF_Normal_Nonworking += 1
            if not renderdb_dic[m_name]['cloneof']: stats_MF_Normal_Nonworking_parents += 1
        # Found in mame2003-plus.xml, machine quizf1 and maybe others.
        elif driver_status == 'protection': pass
        # Are there machines with undefined status?
        elif driver_status == '': pass
        else:
            log_error('Machine {}, unrecognised driver_status {}'.format(m_name, driver_status))
            raise TypeError
    processed_filters += 1
    pDialog.updateProgress(processed_filters)
    for m_name in main_catalog_all['Unusual']:
        driver_status = renderdb_dic[m_name]['driver_status']
        stats_MF_Unusual_Total += 1
        if not renderdb_dic[m_name]['cloneof']: stats_MF_Unusual_Total_parents += 1
        if driver_status == 'good':
            stats_MF_Unusual_Good += 1
            if not renderdb_dic[m_name]['cloneof']: stats_MF_Unusual_Good_parents += 1
        elif driver_status == 'imperfect':
            stats_MF_Unusual_Imperfect += 1
            if not renderdb_dic[m_name]['cloneof']: stats_MF_Unusual_Imperfect_parents += 1
        elif driver_status == 'preliminary':
            stats_MF_Unusual_Nonworking += 1
            if not renderdb_dic[m_name]['cloneof']: stats_MF_Unusual_Nonworking_parents += 1
        elif driver_status == 'protection': pass
        elif driver_status == '': pass
        else:
            log_error('Machine {}, unrecognised driver_status {}'.format(m_name, driver_status))
            raise TypeError
    processed_filters += 1
    pDialog.updateProgress(processed_filters)
    for m_name in main_catalog_all['NoCoin']:
        driver_status = renderdb_dic[m_name]['driver_status']
        stats_MF_Nocoin_Total += 1
        if not renderdb_dic[m_name]['cloneof']: stats_MF_Nocoin_Total_parents += 1
        if driver_status == 'good':
            stats_MF_Nocoin_Good += 1
            if not renderdb_dic[m_name]['cloneof']: stats_MF_Nocoin_Good_parents += 1
        elif driver_status == 'imperfect':
            stats_MF_Nocoin_Imperfect += 1
            if not renderdb_dic[m_name]['cloneof']: stats_MF_Nocoin_Imperfect_parents += 1
        elif driver_status == 'preliminary':
            stats_MF_Nocoin_Nonworking += 1
            if not renderdb_dic[m_name]['cloneof']: stats_MF_Nocoin_Nonworking_parents += 1
        elif driver_status == 'protection': pass
        elif driver_status == '': pass
        else:
            log_error('Machine {}, unrecognised driver_status {}'.format(m_name, driver_status))
            raise TypeError
    processed_filters += 1
    pDialog.updateProgress(processed_filters)
    for m_name in main_catalog_all['Mechanical']:
        driver_status = renderdb_dic[m_name]['driver_status']
        stats_MF_Mechanical_Total += 1
        if not renderdb_dic[m_name]['cloneof']: stats_MF_Mechanical_Total_parents += 1
        if driver_status == 'good':
            stats_MF_Mechanical_Good += 1
            if not renderdb_dic[m_name]['cloneof']: stats_MF_Mechanical_Good_parents += 1
        elif driver_status == 'imperfect':
            stats_MF_Mechanical_Imperfect += 1
            if not renderdb_dic[m_name]['cloneof']: stats_MF_Mechanical_Imperfect_parents += 1
        elif driver_status == 'preliminary':
            stats_MF_Mechanical_Nonworking += 1
            if not renderdb_dic[m_name]['cloneof']: stats_MF_Mechanical_Nonworking_parents += 1
        elif driver_status == 'protection': pass
        elif driver_status == '': pass
        else:
            log_error('Machine {}, unrecognised driver_status {}'.format(m_name, driver_status))
            raise TypeError
    processed_filters += 1
    pDialog.updateProgress(processed_filters)
    for m_name in main_catalog_all['Dead']:
        driver_status = renderdb_dic[m_name]['driver_status']
        stats_MF_Dead_Total += 1
        if not renderdb_dic[m_name]['cloneof']: stats_MF_Dead_Total_parents += 1
        if driver_status == 'good':
            stats_MF_Dead_Good += 1
            if not renderdb_dic[m_name]['cloneof']: stats_MF_Dead_Good_parents += 1
        elif driver_status == 'imperfect':
            stats_MF_Dead_Imperfect += 1
            if not renderdb_dic[m_name]['cloneof']: stats_MF_Dead_Imperfect_parents += 1
        elif driver_status == 'preliminary':
            stats_MF_Dead_Nonworking += 1
            if not renderdb_dic[m_name]['cloneof']: stats_MF_Dead_Nonworking_parents += 1
        elif driver_status == 'protection': pass
        elif driver_status == '': pass
        else:
            log_error('Machine {}, unrecognised driver_status {}'.format(m_name, driver_status))
            raise TypeError
    pDialog.endProgress()

    # --- Update statistics ---
    db_safe_edit(control_dic, 'stats_MF_Normal_Total', stats_MF_Normal_Total)
    db_safe_edit(control_dic, 'stats_MF_Normal_Good', stats_MF_Normal_Good)
    db_safe_edit(control_dic, 'stats_MF_Normal_Imperfect', stats_MF_Normal_Imperfect)
    db_safe_edit(control_dic, 'stats_MF_Normal_Nonworking', stats_MF_Normal_Nonworking)
    db_safe_edit(control_dic, 'stats_MF_Unusual_Total', stats_MF_Unusual_Total)
    db_safe_edit(control_dic, 'stats_MF_Unusual_Good', stats_MF_Unusual_Good)
    db_safe_edit(control_dic, 'stats_MF_Unusual_Imperfect', stats_MF_Unusual_Imperfect)
    db_safe_edit(control_dic, 'stats_MF_Unusual_Nonworking', stats_MF_Unusual_Nonworking)
    db_safe_edit(control_dic, 'stats_MF_Nocoin_Total', stats_MF_Nocoin_Total)
    db_safe_edit(control_dic, 'stats_MF_Nocoin_Good', stats_MF_Nocoin_Good)
    db_safe_edit(control_dic, 'stats_MF_Nocoin_Imperfect', stats_MF_Nocoin_Imperfect)
    db_safe_edit(control_dic, 'stats_MF_Nocoin_Nonworking', stats_MF_Nocoin_Nonworking)
    db_safe_edit(control_dic, 'stats_MF_Mechanical_Total', stats_MF_Mechanical_Total)
    db_safe_edit(control_dic, 'stats_MF_Mechanical_Good', stats_MF_Mechanical_Good)
    db_safe_edit(control_dic, 'stats_MF_Mechanical_Imperfect', stats_MF_Mechanical_Imperfect)
    db_safe_edit(control_dic, 'stats_MF_Mechanical_Nonworking', stats_MF_Mechanical_Nonworking)
    db_safe_edit(control_dic, 'stats_MF_Dead_Total', stats_MF_Dead_Total)
    db_safe_edit(control_dic, 'stats_MF_Dead_Good', stats_MF_Dead_Good)
    db_safe_edit(control_dic, 'stats_MF_Dead_Imperfect', stats_MF_Dead_Imperfect)
    db_safe_edit(control_dic, 'stats_MF_Dead_Nonworking', stats_MF_Dead_Nonworking)

    db_safe_edit(control_dic, 'stats_MF_Normal_Total_parents', stats_MF_Normal_Total_parents)
    db_safe_edit(control_dic, 'stats_MF_Normal_Good_parents', stats_MF_Normal_Good_parents)
    db_safe_edit(control_dic, 'stats_MF_Normal_Imperfect_parents', stats_MF_Normal_Imperfect_parents)
    db_safe_edit(control_dic, 'stats_MF_Normal_Nonworking_parents', stats_MF_Normal_Nonworking_parents)
    db_safe_edit(control_dic, 'stats_MF_Unusual_Total_parents', stats_MF_Unusual_Total_parents)
    db_safe_edit(control_dic, 'stats_MF_Unusual_Good_parents', stats_MF_Unusual_Good_parents)
    db_safe_edit(control_dic, 'stats_MF_Unusual_Imperfect_parents', stats_MF_Unusual_Imperfect_parents)
    db_safe_edit(control_dic, 'stats_MF_Unusual_Nonworking_parents', stats_MF_Unusual_Nonworking_parents)
    db_safe_edit(control_dic, 'stats_MF_Nocoin_Total_parents', stats_MF_Nocoin_Total_parents)
    db_safe_edit(control_dic, 'stats_MF_Nocoin_Good_parents', stats_MF_Nocoin_Good_parents)
    db_safe_edit(control_dic, 'stats_MF_Nocoin_Imperfect_parents', stats_MF_Nocoin_Imperfect_parents)
    db_safe_edit(control_dic, 'stats_MF_Nocoin_Nonworking_parents', stats_MF_Nocoin_Nonworking_parents)
    db_safe_edit(control_dic, 'stats_MF_Mechanical_Total_parents', stats_MF_Mechanical_Total_parents)
    db_safe_edit(control_dic, 'stats_MF_Mechanical_Good_parents', stats_MF_Mechanical_Good_parents)
    db_safe_edit(control_dic, 'stats_MF_Mechanical_Imperfect_parents', stats_MF_Mechanical_Imperfect_parents)
    db_safe_edit(control_dic, 'stats_MF_Mechanical_Nonworking_parents', stats_MF_Mechanical_Nonworking_parents)
    db_safe_edit(control_dic, 'stats_MF_Dead_Total_parents', stats_MF_Dead_Total_parents)
    db_safe_edit(control_dic, 'stats_MF_Dead_Good_parents', stats_MF_Dead_Good_parents)
    db_safe_edit(control_dic, 'stats_MF_Dead_Imperfect_parents', stats_MF_Dead_Imperfect_parents)
    db_safe_edit(control_dic, 'stats_MF_Dead_Nonworking_parents', stats_MF_Dead_Nonworking_parents)

    # --- Update timestamp ---
    db_safe_edit(control_dic, 't_MAME_Catalog_build', time.time())

    # --- Save stuff ------------------------------------------------------------------------------
    db_files = [
        [cache_index_dic, 'MAME cache index', cfg.CACHE_INDEX_PATH.getPath()],
        [control_dic, 'Control dictionary', cfg.MAIN_CONTROL_PATH.getPath()],
    ]
    db_save_files(db_files)
    db_dic_in['cache_index'] = cache_index_dic

# -------------------------------------------------------------------------------------------------
# Software Lists and ROM audit database building function
# -------------------------------------------------------------------------------------------------
#
# https://www.mess.org/mess/swlist_format
# The basic idea (which leads basically the whole format) is that each <software> entry should
# correspond to a game box you could have bought in a shop, and that each <part> entry should
# correspond to a piece (i.e. a cart, a disk or a tape) that you would have found in such a box.
#
# --- Example 1: 32x.xml-chaotix ---
# Stored as: SL_ROMS/32x/chaotix.zip
#
# <part name="cart" interface="_32x_cart">
#   <dataarea name="rom" size="3145728">
#     <rom name="knuckles' chaotix (europe).bin" size="3145728" crc="41d63572" sha1="5c1...922" offset="000000" />
#   </dataarea>
# </part>
#
# --- Example 2: 32x.xml-doom ---
# Stored as: SL_ROMS/32x/doom.zip
#
# <part name="cart" interface="_32x_cart">
#   <feature name="pcb" value="171-6885A" />
#   <dataarea name="rom" size="3145728">
#     <rom name="mpr-17351-f.ic1" size="2097152" crc="e0ef6ebc" sha1="302...79d" offset="000000" />
#     <rom name="mpr-17352-f.ic2" size="1048576" crc="c7079709" sha1="0f2...33b" offset="0x200000" />
#   </dataarea>
# </part>
#
# --- Example 3: a800.xml-diamond3 ---
# Stored as: SL_ROMS/a800/diamond3.zip (all ROMs from all parts)
#
# <part name="cart" interface="a8bit_cart">
#   <feature name="slot" value="a800_diamond" />
#   <dataarea name="rom" size="65536">
#     <rom name="diamond gos v3.0.rom" size="65536" crc="0ead07f8" sha1="e92...730" offset="0" />
#   </dataarea>
# </part>
# <part name="flop1" interface="floppy_5_25">
#   <dataarea name="flop" size="92176">
#     <rom name="diamond paint.atr" size="92176" crc="d2994282" sha1="be8...287" offset="0" />
#   </dataarea>
# </part>
# <part name="flop2" interface="floppy_5_25">
#   <dataarea name="flop" size="92176">
#     <rom name="diamond write.atr" size="92176" crc="e1e5b235" sha1="c3c...db5" offset="0" />
#   </dataarea>
# </part>
# <part name="flop3" interface="floppy_5_25">
#   <dataarea name="flop" size="92176">
#     <rom name="diamond utilities.atr" size="92176" crc="bb48082d" sha1="eb7...4e4" offset="0" />
#   </dataarea>
# </part>
#
# --- Example 4: a2600.xml-harmbios ---
# Stored as: SL_ROMS/a2600/harmbios.zip (all ROMs from all dataareas)
#
# <part name="cart" interface="a2600_cart">
#   <feature name="slot" value="a26_harmony" />
#   <dataarea name="rom" size="0x8000">
#     <rom name="bios_updater_NTSC.cu" size="0x8000" crc="03153eb2" sha1="cd9...009" offset="0" />
#   </dataarea>
#   <dataarea name="bios" size="0x21400">
#     <rom name="hbios_106_NTSC_official_beta.bin" size="0x21400" crc="1e1d237b" sha1="8fd...1da" offset="0" />
#     <rom name="hbios_106_NTSC_beta_2.bin"        size="0x21400" crc="807b86bd" sha1="633...e9d" offset="0" />
#     <rom name="eeloader_104e_PAL60.bin"          size="0x36f8" crc="58845532" sha1="255...71c" offset="0" />
#   </dataarea>
# </part>
#
# --- Example 5: psx.xml-traid ---
# Stored as: SL_CHDS/psx/traid/tomb raider (usa) (v1.6).chd
#
# <part name="cdrom" interface="psx_cdrom">
#   <diskarea name="cdrom">
#     <disk name="tomb raider (usa) (v1.6)" sha1="697...3ac"/>
#   </diskarea>
# </part>
#
# --- Example 6: psx.xml-traida cloneof=traid ---
# Stored as: SL_CHDS/psx/traid/tomb raider (usa) (v1.5).chd
#
# <part name="cdrom" interface="psx_cdrom">
#   <diskarea name="cdrom">
#     <disk name="tomb raider (usa) (v1.5)" sha1="d48...0a9"/>
#   </diskarea>
# </part>
#
# --- Example 7: pico.xml-sanouk5 ---
# Stored as: SL_ROMS/pico/sanouk5.zip (mpr-18458-t.ic1 ROM)
# Stored as: SL_CHDS/pico/sanouk5/imgpico-001.chd
#
# <part name="cart" interface="pico_cart">
#   <dataarea name="rom" size="524288">
#     <rom name="mpr-18458-t.ic1" size="524288" crc="6340c18a" sha1="101..." offset="000000" loadflag="load16_word_swap" />
#   </dataarea>
#   <diskarea name="cdrom">
#     <disk name="imgpico-001" sha1="c93...10d" />
#   </diskarea>
# </part>
#
# -------------------------------------------------------------------------------------------------
# A) One part may have a dataarea, a diskarea, or both.
#
# B) One part may have more than one dataarea with different names.
#
# SL_roms = {
#   'sl_rom_name' : [
#     {
#       'part_name' : string,
#       'part_interface' : string,
#       'dataarea' : [
#         {
#           'name' : string,
#           'roms' : [
#             {
#               'name' : string, 'size' : int, 'crc' : string
#             },
#           ]
#         }
#       ]
#       'diskarea' : [
#         {
#           'name' : string,
#           'disks' : [
#             {
#               'name' : string, 'sha1' : string
#             },
#           ]
#         }
#       ]
#     }, ...
#   ], ...
# }
#
# -------------------------------------------------------------------------------------------------
# --- SL List ROM Audit database ---
#
# A) For each SL ROM entry, create a list of the ROM files and CHD files, names, sizes, crc/sha1
#    and location.
# SL_roms = {
#   'sl_rom_name' : [
#     {
#       'type'     : string,
#       'name'     : string,
#       'size      : int,
#       'crc'      : sting,
#       'location' : string
#     }, ...
#   ], ...
# }

#
# SL_disks = {
#   'sl_rom_name' : [
#     {
#       'type' : string,
#       'name' : string,
#       'sha1' : sting,
#       'location' : string
#     }, ...
#   ], ...
# }
#
def _new_SL_Data_dic():
    return {
        'items'         : {},
        'SL_roms'       : {},
        'display_name'  : '',
        'num_with_ROMs' : 0,
        'num_with_CHDs' : 0,
        'num_items'     : 0,
        'num_parents'   : 0,
        'num_clones'    : 0,
    }

# Get ROMs in dataarea.
def _get_SL_dataarea_ROMs(SL_name, item_name, part_child, dataarea_dic):
    __DEBUG_SL_ROM_PROCESSING = False
    dataarea_num_roms = 0
    for dataarea_child in part_child:
        rom_dic = { 'name' : '', 'size' : '', 'crc'  : '', 'sha1' : '' }
        # Force Python to guess the base of the conversion looking at 0x prefixes.
        size_int = 0
        if 'size' in dataarea_child.attrib:
            size_int = int(dataarea_child.attrib['size'], 0)
        rom_dic['size'] = size_int
        rom_dic['name'] = dataarea_child.attrib['name'] if 'name' in dataarea_child.attrib else ''
        rom_dic['crc']  = dataarea_child.attrib['crc'] if 'crc' in dataarea_child.attrib else ''
        rom_dic['sha1'] = dataarea_child.attrib['sha1'] if 'sha1' in dataarea_child.attrib else ''

        # In the nes.xml SL some ROM names have a trailing dot '.'. For example (MAME 0.196):
        #
        # ROM  131072  028bfc44  nes/kingey/0.prg              OK
        # ROM  131072  1aca7960  nes/kingey/king ver 1.3 vid.  ROM not in ZIP
        #
        # PD torrents do not have the trailing dot because this files cause trouble in Windows.
        # To correctly audit PD torrents, remove the trailing dot from filenames.
        # Have a look here http://forum.pleasuredome.org.uk/index.php?showtopic=32701&p=284925
        # I will create a PR to MAME repo to fix these names (and then next couple of lines must
        # be commented).
        if len(rom_dic['name']) > 2 and rom_dic['name'][-1] == '.':
            rom_dic['name'] = rom_dic['name'][:-1]

        # Some CRCs are in upper case. Store always lower case in AML DB.
        if rom_dic['crc']: rom_dic['crc'] = rom_dic['crc'].lower()

        # Just in case there are SHA1 hashes in upper case (not verified).
        if rom_dic['sha1']: rom_dic['sha1'] = rom_dic['sha1'].lower()

        # If ROM has attribute status="nodump" then ignore this ROM.
        if 'status' in dataarea_child.attrib:
            status = dataarea_child.attrib['status']
            if status == 'nodump':
                if __DEBUG_SL_ROM_PROCESSING:
                    log_debug('SL "{}" item "{}" status="nodump". Skipping ROM.'.format(SL_name, item_name))
                continue
            elif status == 'baddump':
                if __DEBUG_SL_ROM_PROCESSING:
                    log_debug('SL "{}" item "{}" status="baddump".'.format(SL_name, item_name))
                pass
            else:
                log_error('SL "{}" item "{}" Unknown status = {}'.format(SL_name, item_name, status))
                raise CriticalError('DEBUG')

        # Fix "fake" SL ROMs with loadflag="continue".
        # For example, SL neogeo, SL item aof
        if 'loadflag' in dataarea_child.attrib:
            loadflag = dataarea_child.attrib['loadflag']
            if loadflag == 'continue':
                # This ROM is not valid (not a valid ROM file).
                # Size must be added to previous ROM.
                if __DEBUG_SL_ROM_PROCESSING:
                    log_debug('SL "{}" item "{}" loadflag="continue" case. Adding size {} to previous ROM.'.format(
                        SL_name, item_name, rom_dic['size']))
                previous_rom = dataarea_dic['roms'][-1]
                previous_rom['size'] += rom_dic['size']
                continue
            elif loadflag == 'ignore':
                if rom_dic['size'] > 0:
                    if __DEBUG_SL_ROM_PROCESSING:
                        log_debug('SL "{}" item "{}" loadflag="ignore" case. Adding size {} to previous ROM.'.format(
                            SL_name, item_name, rom_dic['size']))
                    previous_rom = dataarea_dic['roms'][-1]
                    previous_rom['size'] += rom_dic['size']
                else:
                    if __DEBUG_SL_ROM_PROCESSING:
                        log_debug('SL "{}" item "{}" loadflag="ignore" case and size = 0. Skipping ROM.'.format(
                            SL_name, item_name))
                continue
            elif loadflag == 'reload':
                if __DEBUG_SL_ROM_PROCESSING:
                    log_debug('SL "{}" item "{}" loadflag="reload" case. Skipping ROM.'.format(
                        SL_name, item_name))
                continue
            elif loadflag == 'reload_plain':
                if __DEBUG_SL_ROM_PROCESSING:
                    log_debug('SL "{}" item "{}" loadflag="reload_plain" case. Skipping ROM.'.format(
                        SL_name, item_name))
                continue
            elif loadflag == 'fill':
                if __DEBUG_SL_ROM_PROCESSING:
                    log_debug('SL "{}" item "{}" loadflag="fill" case. Skipping ROM.'.format(
                        SL_name, item_name))
                continue
            elif loadflag == 'load16_word_swap':
                pass
            elif loadflag == 'load16_byte':
                pass
            elif loadflag == 'load32_word':
                pass
            elif loadflag == 'load32_byte':
                pass
            elif loadflag == 'load32_word_swap':
                pass
            else:
                t = 'SL "{}" item "{}" unknown loadflag="{}"'.format(SL_name, item_name, loadflag)
                log_error(t)
                raise ValueError(t)

        # --- Add ROM to DB ---
        dataarea_dic['roms'].append(rom_dic)
        dataarea_num_roms += 1

        # --- DEBUG: Error if rom has merge attribute ---
        if 'merge' in dataarea_child.attrib:
            log_error('SL {}, Item {}'.format(SL_name, item_name))
            log_error('ROM {} has merge attribute'.format(dataarea_child.attrib['name']))
            raise CriticalError('DEBUG')

    return dataarea_num_roms

# Get CHDs in diskarea.
def _get_SL_dataarea_CHDs(SL_name, item_name, part_child, diskarea_dic):
    da_num_disks = 0
    for diskarea_child in part_child:
        disk_dic = { 'name' : '', 'sha1' : '' }
        disk_dic['name'] = diskarea_child.attrib['name'] if 'name' in diskarea_child.attrib else ''
        disk_dic['sha1'] = diskarea_child.attrib['sha1'] if 'sha1' in diskarea_child.attrib else ''
        diskarea_dic['disks'].append(disk_dic)
        da_num_disks += 1

    return da_num_disks

def _mame_load_SL_XML(xml_filename):
    __debug_xml_parser = False
    SLData = _new_SL_Data_dic()

    # If file does not exist return empty dictionary.
    if not os.path.isfile(xml_filename): return SLData
    (head, SL_name) = os.path.split(xml_filename)

    # Parse using ElementTree.
    # If XML has errors (invalid characters, etc.) this will rais exception 'err'
    # log_debug('_mame_load_SL_XML() Loading XML file "{}"'.format(xml_filename))
    try:
        xml_tree = ET.parse(xml_filename)
    except:
        return SLData
    xml_root = xml_tree.getroot()
    SL_desc = xml_root.attrib['description']
    # Substitute SL description (long name).
    if SL_desc in SL_better_name_dic:
        old_SL_desc = SL_desc
        SL_desc = SL_better_name_dic[SL_desc]
        log_debug('Substitute SL "{}" with "{}"'.format(old_SL_desc, SL_desc))
    SLData['display_name'] = SL_desc
    for root_element in xml_root:
        if __debug_xml_parser: log_debug('Root child {}'.format(root_element.tag))
        # Only process 'software' elements
        if root_element.tag != 'software':
            log_warning('In SL {}, unrecognised XML tag <{}>'.format(SL_name, root_element.tag))
            continue
        SL_item = db_new_SL_ROM()
        SL_rom_list = []
        num_roms = 0
        num_disks = 0
        item_name = root_element.attrib['name']
        if 'cloneof' in root_element.attrib: SL_item['cloneof'] = root_element.attrib['cloneof']
        if 'romof' in root_element.attrib:
            raise TypeError('SL {} item {}, "romof" in root_element.attrib'.format(SL_name, item_name))

        for rom_child in root_element:
            # By default read strings
            xml_text = rom_child.text if rom_child.text is not None else ''
            xml_tag  = rom_child.tag
            if __debug_xml_parser: log_debug('{} --> {}'.format(xml_tag, xml_text))

            # --- Only pick tags we want ---
            if xml_tag == 'description' or xml_tag == 'year' or xml_tag == 'publisher':
                SL_item[xml_tag] = xml_text

            elif xml_tag == 'part':
                # <part name="cart" interface="_32x_cart">
                part_dic = db_new_SL_ROM_part()
                part_dic['name'] = rom_child.attrib['name']
                part_dic['interface'] = rom_child.attrib['interface']
                SL_item['parts'].append(part_dic)
                SL_roms_dic = {
                    'part_name'      : rom_child.attrib['name'],
                    'part_interface' : rom_child.attrib['interface']
                }

                # --- Count number of <dataarea> and <diskarea> tags inside this <part tag> ---
                num_dataarea = 0
                num_diskarea = 0
                for part_child in rom_child:
                    if part_child.tag == 'dataarea':
                        dataarea_dic = { 'name' : part_child.attrib['name'], 'roms' : [] }
                        da_num_roms = _get_SL_dataarea_ROMs(SL_name, item_name, part_child, dataarea_dic)
                        if da_num_roms > 0:
                            # >> dataarea is valid ONLY if it contains valid ROMs
                            num_dataarea += 1
                            num_roms += da_num_roms
                        if 'dataarea' not in SL_roms_dic: SL_roms_dic['dataarea'] = []
                        SL_roms_dic['dataarea'].append(dataarea_dic)
                    elif part_child.tag == 'diskarea':
                        diskarea_dic = { 'name' : part_child.attrib['name'], 'disks' : [] }
                        da_num_disks = _get_SL_dataarea_CHDs(SL_name, item_name, part_child, diskarea_dic)
                        if da_num_disks > 0:
                            # >> diskarea is valid ONLY if it contains valid CHDs
                            num_diskarea += 1
                            num_disks += da_num_disks
                        if 'diskarea' not in SL_roms_dic: SL_roms_dic['diskarea'] = []
                        SL_roms_dic['diskarea'].append(diskarea_dic)
                    elif part_child.tag == 'feature':
                        pass
                    elif part_child.tag == 'dipswitch':
                        pass
                    else:
                        raise TypeError('SL {} item {}, inside <part>, unrecognised tag <{}>'.format(
                            SL_name, item_name, part_child.tag))
                # --- Add ROMs/disks ---
                SL_rom_list.append(SL_roms_dic)

                # --- DEBUG/Research code ---
                # if num_dataarea > 1:
                #     log_error('{} -> num_dataarea = {}'.format(item_name, num_dataarea))
                #     raise TypeError('DEBUG')
                # if num_diskarea > 1:
                #     log_error('{} -> num_diskarea = {}'.format(item_name, num_diskarea))
                #     raise TypeError('DEBUG')
                # if num_dataarea and num_diskarea:
                #     log_error('{} -> num_dataarea = {}'.format(item_name, num_dataarea))
                #     log_error('{} -> num_diskarea = {}'.format(item_name, num_diskarea))
                #     raise TypeError('DEBUG')

        # --- Finished processing of <software> element ---
        SLData['num_items'] += 1
        if SL_item['cloneof']: SLData['num_clones'] += 1
        else:                  SLData['num_parents'] += 1
        if num_roms:
            SL_item['hasROMs'] = True
            SL_item['status_ROM'] = '?'
            SLData['num_with_ROMs'] += 1
        else:
            SL_item['hasROMs'] = False
            SL_item['status_ROM'] = '-'
        if num_disks:
            SL_item['hasCHDs'] = True
            SL_item['status_CHD'] = '?'
            SLData['num_with_CHDs'] += 1
        else:
            SL_item['hasCHDs'] = False
            SL_item['status_CHD'] = '-'

        # Add <software> item (SL_item) to database and software ROM/CHDs to database.
        SLData['items'][item_name] = SL_item
        SLData['SL_roms'][item_name] = SL_rom_list

    return SLData

def _get_SL_parent_ROM_dic(parent_name, SL_ROMs):
    parent_rom_dic = {}
    for part_dic in SL_ROMs[parent_name]:
        if not 'dataarea' in part_dic: continue
        for dataarea_dic in part_dic['dataarea']:
            for rom_dic in dataarea_dic['roms']:
                parent_rom_dic[rom_dic['crc']] = rom_dic['name']

    return parent_rom_dic

def _get_SL_ROM_location(rom_set, SL_name, SL_item_name, rom_dic, SL_Items, parent_rom_dic):
    # Some SL invalid ROMs do not have name attribute (and not CRC and SHA1).
    # For those, set the location to empty.
    if not rom_dic['name']: return ''

    # In the SL ROM MERGED set all ROMs are stored in the parent ZIP file:
    #
    # PATH/32x/chaotix.zip/knuckles' chaotix (europe).bin
    # PATH/32x/chaotix.zip/chaotixju/chaotix ~ knuckles' chaotix (japan, usa).bin
    # PATH/32x/chaotix.zip/chaotixjup/knuckles' chaotix (prototype 214 - feb 14, 1995, 06.46).bin
    #
    if rom_set == 'MERGED':
        cloneof = SL_Items[SL_item_name]['cloneof']
        if cloneof:
            location = SL_name + '/' + cloneof + '/' + SL_item_name + '/' + rom_dic['name']
        else:
            location = SL_name + '/' + SL_item_name + '/' + rom_dic['name']

    # In the SL ROM SPLIT set each item ROMs are in their own file:
    #
    # PATH/32x/chaotix.zip/knuckles' chaotix (europe).bin
    # PATH/32x/chaotixju.zip/chaotix ~ knuckles' chaotix (japan, usa).bin
    # PATH/32x/chaotixjup.zip/knuckles' chaotix (prototype 214 - feb 14, 1995, 06.46).bin
    #
    # NOTE that ClrMAME Pro (and hence PD torrents) do implicit ROM merging. SL XMLs do not have
    #      the merge attribute. However, an implicit ROM merge is done if a ROM with the same
    #      CRC is found in the parent. Implicit merging only affects clones. A dictionary
    #      of the parent ROMs with key the CRC hash and value the ROM name is required.
    #
    elif rom_set == 'SPLIT':
        cloneof = SL_Items[SL_item_name]['cloneof']
        if cloneof:
            if rom_dic['crc'] in parent_rom_dic:
                location = SL_name + '/' + cloneof + '/' + parent_rom_dic[rom_dic['crc']]
            else:
                location = SL_name + '/' + SL_item_name + '/' + rom_dic['name']
        else:
            location = SL_name + '/' + SL_item_name + '/' + rom_dic['name']

    elif rom_set == 'NONMERGED':
        location = SL_name + '/' + SL_item_name + '/' + rom_dic['name']

    else:
        raise TypeError

    return location

def _get_SL_CHD_location(chd_set, SL_name, SL_item_name, disk_dic, SL_Items):
    # In the SL CHD MERGED set all CHDs are in the directory of the parent:
    #
    # ffant9  --> parent with 4 DISKS (v1.1)
    # ffant9a --> parent with 4 DISKS (v1.0)
    #
    # [parent traid]   PATH/psx/traid/tomb raider (usa) (v1.6).chd
    # [clone  traida]  PATH/psx/traid/tomb raider (usa) (v1.5).chd
    # [clone  traiddm] PATH/psx/traid/tr1.chd
    #
    if chd_set == 'MERGED':
        cloneof = SL_Items[SL_item_name]['cloneof']
        archive_name = cloneof if cloneof else SL_item_name
        location = SL_name + '/' + archive_name + '/' + disk_dic['name']

    # In the SL CHD SPLIT set CHD of each machine are in their own directory.
    # This is not confirmed since I do not have the PD DAT file for the SL CHD SPLIT set.
    #
    # [parent traid]   PATH/psx/traid/tomb raider (usa) (v1.6).chd
    # [clone  traida]  PATH/psx/traida/tomb raider (usa) (v1.5).chd
    # [clone  traiddm] PATH/psx/traiddm/tr1.chd
    #
    elif chd_set == 'SPLIT':
        location = SL_name + '/' + SL_rom + '/' + disk_dic['name']

    else:
        raise TypeError

    return location

# -------------------------------------------------------------------------------------------------
#
# Checks for errors before scanning for SL ROMs.
# Display a Kodi dialog if an error is found.
#
def mame_check_before_build_SL_databases(cfg, st_dic, control_dic):
    kodi_reset_status(st_dic)

    # --- Error checks ---
    if not cfg.settings['SL_hash_path']:
        t = ('Software Lists hash path not set. '
             'Open AML addon settings and configure the location of the MAME hash path in the '
             '"Paths" tab.')
        kodi_set_error_status(st_dic, t)
        return

    if not cfg.MAIN_DB_PATH.exists():
        t = ('MAME Main database not found. '
            'Open AML addon settings and configure the location of the MAME executable in the '
            '"Paths" tab.')
        kodi_set_error_status(st_dic, t)
        return

#
# Modifies dictionary db_dic_in.
#
# SL_catalog_dic = { 'name' : {
#     'display_name': u'',
#     'num_clones' : int,
#     'num_items' : int,
#     'num_parents' : int,
#     'num_with_CHDs' : int,
#     'num_with_ROMs' : int,
#     'rom_DB_noext' : u''
#     },
# }
#
# Saves:
# SL_INDEX_PATH,
# SL_MACHINES_PATH,
# SL_PCLONE_DIC_PATH,
# per-SL database                       (32x.json)
# per-SL database                       (32x_ROMs.json)
# per-SL ROM audit database             (32x_ROM_audit.json)
# per-SL item archives (ROMs and CHDs)  (32x_ROM_archives.json)
#
def mame_build_SoftwareLists_databases(cfg, st_dic, db_dic_in):
    control_dic = db_dic_in['control_dic']
    machines = db_dic_in['machines']
    renderdb_dic = db_dic_in['renderdb']

    SL_dir_FN = FileName(cfg.settings['SL_hash_path'])
    log_debug('mame_build_SoftwareLists_databases() SL_dir_FN "{}"'.format(SL_dir_FN.getPath()))

    # --- Scan all XML files in Software Lists directory and save SL catalog and SL databases ---
    log_info('Processing Software List XML files...')
    SL_file_list = SL_dir_FN.scanFilesInPath('*.xml')
    # DEBUG code for development, only process first SL file (32x).
    # SL_file_list = [ sorted(SL_file_list)[0] ]
    total_SL_files = len(SL_file_list)
    num_SL_with_ROMs = 0
    num_SL_with_CHDs = 0
    SL_catalog_dic = {}
    processed_files = 0
    diag_line = 'Building Sofware Lists item databases...'
    pDialog = KodiProgressDialog()
    pDialog.startProgress(diag_line, total_SL_files)
    for file in sorted(SL_file_list):
        # Progress dialog
        FN = FileName(file)
        pDialog.updateProgress(processed_files,
            '{}\nSoftware List [COLOR orange]{}[/COLOR]'.format(diag_line, FN.getBase()))

        # Open software list XML and parse it. Then, save data fields we want in JSON.
        # log_debug('mame_build_SoftwareLists_databases() Processing "{}"'.format(file))
        SL_path_FN = FileName(file)
        SLData = _mame_load_SL_XML(SL_path_FN.getPath())
        utils_write_JSON_file(cfg.SL_DB_DIR.pjoin(FN.getBaseNoExt() + '_items.json').getPath(),
            SLData['items'], verbose = False)
        utils_write_JSON_file(cfg.SL_DB_DIR.pjoin(FN.getBaseNoExt() + '_ROMs.json').getPath(),
            SLData['SL_roms'], verbose = False)

        # Add software list to catalog
        num_SL_with_ROMs += SLData['num_with_ROMs']
        num_SL_with_CHDs += SLData['num_with_CHDs']
        SL = {
            'display_name'  : SLData['display_name'],
            'num_with_ROMs' : SLData['num_with_ROMs'],
            'num_with_CHDs' : SLData['num_with_CHDs'],
            'num_items'     : SLData['num_items'],
            'num_parents'   : SLData['num_parents'],
            'num_clones'    : SLData['num_clones'],
            'rom_DB_noext'  : FN.getBaseNoExt(),
        }
        SL_catalog_dic[FN.getBaseNoExt()] = SL

        # Update progress
        processed_files += 1
    pDialog.endProgress()

    # --- Make the SL ROM/CHD unified Audit databases ---
    log_info('Building Software List ROM Audit database...')
    rom_set = ['MERGED', 'SPLIT', 'NONMERGED'][cfg.settings['SL_rom_set']]
    chd_set = ['MERGED', 'SPLIT', 'NONMERGED'][cfg.settings['SL_chd_set']]
    log_info('mame_build_SoftwareLists_databases() SL ROM set is {}'.format(rom_set))
    log_info('mame_build_SoftwareLists_databases() SL CHD set is {}'.format(chd_set))
    total_files = len(SL_file_list)
    processed_files = 0
    stats_audit_SL_items_runnable = 0
    stats_audit_SL_items_with_arch = 0
    stats_audit_SL_items_with_arch_ROM = 0
    stats_audit_SL_items_with_CHD = 0
    diag_line = 'Building Software List ROM audit databases...'
    pDialog.startProgress(diag_line, total_files)
    for file in sorted(SL_file_list):
        # Update progress
        FN = FileName(file)
        SL_name = FN.getBaseNoExt()
        pDialog.updateProgress(processed_files, '{}\nSoftware List [COLOR orange]{}[/COLOR]'.format(
            diag_line, FN.getBase()))

        # Filenames of the databases
        # log_debug('mame_build_SoftwareLists_databases() Processing "{}"'.format(file))
        SL_Items_DB_FN = cfg.SL_DB_DIR.pjoin(FN.getBaseNoExt() + '_items.json')
        SL_ROMs_DB_FN = cfg.SL_DB_DIR.pjoin(FN.getBaseNoExt() + '_ROMs.json')
        SL_ROM_Audit_DB_FN = cfg.SL_DB_DIR.pjoin(FN.getBaseNoExt() + '_ROM_audit.json')
        SL_Soft_Archives_DB_FN = cfg.SL_DB_DIR.pjoin(FN.getBaseNoExt() + '_ROM_archives.json')
        SL_Items = utils_load_JSON_file(SL_Items_DB_FN.getPath(), verbose = False)
        SL_ROMs = utils_load_JSON_file(SL_ROMs_DB_FN.getPath(), verbose = False)

        # --- First add the SL item ROMs to the audit database ---
        SL_Audit_ROMs_dic = {}
        for SL_item_name in SL_ROMs:
            # >> If SL item is a clone then create parent_rom_dic. This is only needed in the
            # >> SPLIT set, so current code is a bit inefficient for other sets.
            # >> key : CRC -> value : rom name
            cloneof = SL_Items[SL_item_name]['cloneof']
            if cloneof:
                parent_rom_dic = _get_SL_parent_ROM_dic(cloneof, SL_ROMs)
            else:
                parent_rom_dic = {}

            # >> Iterate Parts in a SL Software item. Then iterate dataareas on each part.
            # >> Finally, iterate ROM on each dataarea.
            set_roms = []
            for part_dic in SL_ROMs[SL_item_name]:
                if not 'dataarea' in part_dic: continue
                for dataarea_dic in part_dic['dataarea']:
                    for rom_dic in dataarea_dic['roms']:
                        location = _get_SL_ROM_location(rom_set, SL_name, SL_item_name,
                            rom_dic, SL_Items, parent_rom_dic)
                        rom_audit_dic = db_new_SL_ROM_audit_dic()
                        rom_audit_dic['type']     = ROM_TYPE_ROM
                        rom_audit_dic['name']     = rom_dic['name']
                        rom_audit_dic['size']     = rom_dic['size']
                        rom_audit_dic['crc']      = rom_dic['crc']
                        rom_audit_dic['location'] = location
                        set_roms.append(rom_audit_dic)
            SL_Audit_ROMs_dic[SL_item_name] = set_roms

        # --- Second add the SL item CHDs to the audit database ---
        for SL_item_name in SL_ROMs:
            set_chds = []
            for part_dic in SL_ROMs[SL_item_name]:
                if not 'diskarea' in part_dic: continue
                for diskarea_dic in part_dic['diskarea']:
                    for disk_dic in diskarea_dic['disks']:
                        location = _get_SL_CHD_location(chd_set, SL_name, SL_item_name, disk_dic, SL_Items)
                        disk_audit_dic = db_new_SL_DISK_audit_dic()
                        disk_audit_dic['type']     = ROM_TYPE_DISK
                        disk_audit_dic['name']     = disk_dic['name']
                        disk_audit_dic['sha1']     = disk_dic['sha1']
                        disk_audit_dic['location'] = location
                        set_chds.append(disk_audit_dic)
            # >> Extend ROM list with CHDs.
            if SL_item_name in SL_Audit_ROMs_dic:
                SL_Audit_ROMs_dic[SL_item_name].extend(set_chds)
            else:
                SL_Audit_ROMs_dic[SL_item_name] =  set_chds

        # --- Machine archives ---
        # There is not ROMs and CHDs sets for Software List Items (not necessary).
        SL_Item_Archives_dic = {}
        for SL_item_name in SL_Audit_ROMs_dic:
            rom_list = SL_Audit_ROMs_dic[SL_item_name]
            machine_rom_archive_set = set()
            machine_chd_archive_set = set()
            # --- Iterate ROMs/CHDs ---
            for rom in rom_list:
                if rom['type'] == ROM_TYPE_DISK:
                    # >> Skip invalid CHDs
                    if not rom['sha1']: continue
                    chd_name = rom['location']
                    machine_chd_archive_set.add(chd_name)
                else:
                    # >> Skip invalid ROMs
                    if not rom['crc']: continue
                    rom_str_list = rom['location'].split('/')
                    zip_name = rom_str_list[0] + '/' + rom_str_list[1]
                    machine_rom_archive_set.add(zip_name)
            SL_Item_Archives_dic[SL_item_name] = {
                'ROMs' : list(machine_rom_archive_set),
                'CHDs' : list(machine_chd_archive_set)
            }
            # --- SL Audit database statistics ---
            stats_audit_SL_items_runnable += 1
            if SL_Item_Archives_dic[SL_item_name]['ROMs'] or SL_Item_Archives_dic[SL_item_name]['CHDs']:
                stats_audit_SL_items_with_arch += 1
            if SL_Item_Archives_dic[SL_item_name]['ROMs']: stats_audit_SL_items_with_arch_ROM += 1
            if SL_Item_Archives_dic[SL_item_name]['CHDs']: stats_audit_SL_items_with_CHD += 1

        # --- Save databases ---
        utils_write_JSON_file(SL_ROM_Audit_DB_FN.getPath(), SL_Audit_ROMs_dic, verbose = False)
        utils_write_JSON_file(SL_Soft_Archives_DB_FN.getPath(), SL_Item_Archives_dic, verbose = False)
        processed_files += 1
    pDialog.endProgress()

    # --- Make SL Parent/Clone databases ---
    log_info('Building Software List PClone list...')
    total_files = len(SL_catalog_dic)
    processed_files = 0
    SL_PClone_dic = {}
    total_SL_XML_files = 0
    total_SL_software_items = 0
    diag_line = 'Building Software List PClone list...'
    pDialog.startProgress(diag_line, total_files)
    for sl_name in sorted(SL_catalog_dic):
        pDialog.updateProgress(processed_files, '{}\nSoftware List [COLOR orange]{}[/COLOR]'.format(
            diag_line, sl_name))
        total_SL_XML_files += 1
        pclone_dic = {}
        SL_database_FN = cfg.SL_DB_DIR.pjoin(sl_name + '_items.json')
        ROMs = utils_load_JSON_file(SL_database_FN.getPath(), verbose = False)
        for rom_name in ROMs:
            total_SL_software_items += 1
            ROM = ROMs[rom_name]
            if ROM['cloneof']:
                parent_name = ROM['cloneof']
                if parent_name not in pclone_dic: pclone_dic[parent_name] = []
                pclone_dic[parent_name].append(rom_name)
            else:
                if rom_name not in pclone_dic: pclone_dic[rom_name] = []
        SL_PClone_dic[sl_name] = pclone_dic
        processed_files += 1
    pDialog.endProgress()

    # --- Make a list of machines that can launch each SL ---
    log_info('Making Software List machine list...')
    total_SL = len(SL_catalog_dic)
    processed_SL = 0
    SL_machines_dic = {}
    diag_line = 'Building Software List machine list...'
    pDialog.startProgress(diag_line, total_SL)
    for SL_name in sorted(SL_catalog_dic):
        pDialog.updateProgress(processed_SL, '{}\nSoftware List [COLOR orange]{}[/COLOR]'.format(
            diag_line, SL_name))
        SL_machine_list = []
        for machine_name in machines:
            # if not machines[machine_name]['softwarelists']: continue
            for machine_SL_name in machines[machine_name]['softwarelists']:
                if machine_SL_name == SL_name:
                    SL_machine_dic = {
                        'machine'     : machine_name,
                        'description' : renderdb_dic[machine_name]['description'],
                        'devices'     : machines[machine_name]['devices']
                    }
                    SL_machine_list.append(SL_machine_dic)
        SL_machines_dic[SL_name] = SL_machine_list
        processed_SL += 1
    pDialog.endProgress()

    # --- Empty SL asset DB ---
    log_info('Making Software List (empty) asset databases...')
    total_SL = len(SL_catalog_dic)
    processed_SL = 0
    diag_line = 'Building Software List (empty) asset databases...'
    pDialog.startProgress(diag_line, total_SL)
    for SL_name in sorted(SL_catalog_dic):
        pDialog.updateProgress(processed_SL, '{}\nSoftware List [COLOR orange]{}[/COLOR]'.format(
            diag_line, SL_name))

        # --- Load SL databases ---
        file_name = SL_catalog_dic[SL_name]['rom_DB_noext'] + '_items.json'
        SL_DB_FN = cfg.SL_DB_DIR.pjoin(file_name)
        SL_roms = utils_load_JSON_file(SL_DB_FN.getPath(), verbose = False)
        assets_file_name = SL_catalog_dic[SL_name]['rom_DB_noext'] + '_assets.json'
        SL_asset_DB_FN = cfg.SL_DB_DIR.pjoin(assets_file_name)

        # --- Second pass: substitute artwork ---
        SL_assets_dic = {}
        for rom_key in sorted(SL_roms):
            SL_assets_dic[rom_key] = db_new_SL_asset()

        # --- Write SL asset JSON ---
        utils_write_JSON_file(SL_asset_DB_FN.getPath(), SL_assets_dic, verbose = False)
        processed_SL += 1
    pDialog.endProgress()

    # --- Create properties database with default values ---
    # --- Make SL properties DB ---
    # >> Allows customisation of every SL list window
    # >> Not used at the moment -> Global properties
    # SL_properties_dic = {}
    # for sl_name in SL_catalog_dic:
    #     # 'vm' : VIEW_MODE_NORMAL or VIEW_MODE_ALL
    #     prop_dic = {'vm' : VIEW_MODE_NORMAL}
    #     SL_properties_dic[sl_name] = prop_dic
    # utils_write_JSON_file(cfg.SL_MACHINES_PROP_PATH.getPath(), SL_properties_dic)
    # log_info('SL_properties_dic has {} items'.format(len(SL_properties_dic)))

    # >> One of the MAME catalogs has changed, and so the property names.
    # >> Not used at the moment -> Global properties
    # mame_properties_dic = {}
    # for catalog_name in CATALOG_NAME_LIST:
    #     catalog_dic = db_get_cataloged_dic_parents(cfg, catalog_name)
    #     for category_name in sorted(catalog_dic):
    #         prop_key = '{} - {}'.format(catalog_name, category_name)
    #         mame_properties_dic[prop_key] = {'vm' : VIEW_MODE_NORMAL}
    # utils_write_JSON_file(cfg.MAIN_PROPERTIES_PATH.getPath(), mame_properties_dic)
    # log_info('mame_properties_dic has {} items'.format(len(mame_properties_dic)))

    # -----------------------------------------------------------------------------
    # Update MAME control dictionary
    # -----------------------------------------------------------------------------
    # --- SL item database ---
    db_safe_edit(control_dic, 'stats_SL_XML_files', total_SL_XML_files)
    db_safe_edit(control_dic, 'stats_SL_software_items', total_SL_software_items)
    db_safe_edit(control_dic, 'stats_SL_items_with_ROMs', num_SL_with_ROMs)
    db_safe_edit(control_dic, 'stats_SL_items_with_CHDs', num_SL_with_CHDs)

    # --- SL audit database statistics ---
    db_safe_edit(control_dic, 'stats_audit_SL_items_runnable', stats_audit_SL_items_runnable)
    db_safe_edit(control_dic, 'stats_audit_SL_items_with_arch', stats_audit_SL_items_with_arch)
    db_safe_edit(control_dic, 'stats_audit_SL_items_with_arch_ROM', stats_audit_SL_items_with_arch_ROM)
    db_safe_edit(control_dic, 'stats_audit_SL_items_with_CHD', stats_audit_SL_items_with_CHD)

    # --- SL build timestamp ---
    db_safe_edit(control_dic, 't_SL_DB_build', time.time())

    # --- Save modified/created stuff in this function ---
    if OPTION_LOWMEM_WRITE_JSON:
        json_write_func = utils_write_JSON_file_lowmem
        log_debug('Using utils_write_JSON_file_lowmem() JSON writer')
    else:
        json_write_func = utils_write_JSON_file
        log_debug('Using utils_write_JSON_file() JSON writer')
    db_files = [
        # Fix this list of files!!!
        [SL_catalog_dic, 'Software Lists index', cfg.SL_INDEX_PATH.getPath()],
        [SL_PClone_dic, 'Software Lists P/Clone', cfg.SL_PCLONE_DIC_PATH.getPath()],
        [SL_machines_dic, 'Software Lists machines', cfg.SL_MACHINES_PATH.getPath()],
        # Save control_dic after everything is saved.
        [control_dic, 'Control dictionary', cfg.MAIN_CONTROL_PATH.getPath()],
    ]
    db_save_files(db_files, json_write_func)
    db_dic_in['SL_index'] = SL_catalog_dic
    db_dic_in['SL_machines'] = SL_machines_dic
    db_dic_in['SL_PClone_dic'] = SL_PClone_dic

# -------------------------------------------------------------------------------------------------
# ROM/CHD and asset scanner
# -------------------------------------------------------------------------------------------------
#
# Checks for errors before scanning for SL ROMs.
# Display a Kodi dialog if an error is found.
#
def mame_check_before_scan_MAME_ROMs(cfg, st_dic, options_dic, control_dic):
    log_info('mame_check_before_scan_MAME_ROMs() Starting...')
    kodi_reset_status(st_dic)

    # ROM scanning is mandatory, even if ROM directory is empty.
    # Get paths and check they exist.
    if cfg.settings['op_mode'] == OP_MODE_VANILLA:
        rom_path = cfg.settings['rom_path_vanilla']
    elif cfg.settings['op_mode'] == OP_MODE_RETRO_MAME2003PLUS:
        rom_path = cfg.settings['rom_path_2003_plus']
    else:
        raise TypeError('Unknown op_mode "{}"'.format(cfg.settings['op_mode']))
    if not rom_path:
        kodi_set_error_status(st_dic, 'ROM directory not configured. Aborting scanner.')
        return
    ROM_path_FN = FileName(rom_path)
    if not ROM_path_FN.isdir():
        kodi_set_error_status(st_dic, 'ROM directory does not exist. Aborting scanner.')
        return

    # Scanning of CHDs is optional.
    if cfg.settings['chd_path']:
        CHD_path_FN = FileName(cfg.settings['chd_path'])
        if not CHD_path_FN.isdir():
            kodi_dialog_OK('CHD directory does not exist. CHD scanning disabled.')
            options_dic['scan_CHDs'] = False
        else:
            options_dic['scan_CHDs'] = True
    else:
        kodi_dialog_OK('CHD directory not configured. CHD scanning disabled.')
        options_dic['scan_CHDs'] = False

    # Scanning of Samples is optional.
    if cfg.settings['samples_path']:
        Samples_path_FN = FileName(cfg.settings['samples_path'])
        if not Samples_path_FN.isdir():
            kodi_dialog_OK('Samples directory does not exist. Samples scanning disabled.')
            options_dic['scan_Samples'] = False
        else:
            options_dic['scan_Samples'] = True
    else:
        kodi_dialog_OK('Samples directory not configured. Samples scanning disabled.')
        options_dic['scan_Samples'] = False

#
# Saves control_dic and assets_dic.
#
# PROBLEM with samples scanning.
# Most samples are stored in ZIP files. However, the samples shipped with MAME executable
# are uncompressed:
#   MAME_DIR/samples/floppy/35_seek_12ms.wav
#   MAME_DIR/samples/floppy/35_seek_20ms.wav
#   ...
#   MAME_DIR/samples/MM1_keyboard/beep.wav
#   MAME_DIR/samples/MM1_keyboard/power_switch.wav
#
def mame_scan_MAME_ROMs(cfg, st_dic, options_dic, db_dic_in):
    # --- Convenient variables for databases ---
    control_dic = db_dic_in['control_dic']
    machines = db_dic_in['machines']
    renderdb = db_dic_in['renderdb']
    assetdb = db_dic_in['assetdb']
    machine_archives_dic = db_dic_in['machine_archives']
    # ROM_ZIP_list = db_dic_in['ROM_ZIP_list']
    # Sample_ZIP_list = db_dic_in['Sample_ZIP_list']
    # CHD_list = db_dic_in['CHD_archive_list']

    log_info('mame_scan_MAME_ROMs() Starting...')
    kodi_reset_status(st_dic)

    # At this point paths have been verified and exists.
    if cfg.settings['op_mode'] == OP_MODE_VANILLA:
        rom_path = cfg.settings['rom_path_vanilla']
    elif cfg.settings['op_mode'] == OP_MODE_RETRO_MAME2003PLUS:
        rom_path = cfg.settings['rom_path_2003_plus']
    else:
        raise TypeError('Unknown op_mode "{}"'.format(cfg.settings['op_mode']))
    ROM_path_FN = FileName(rom_path)
    log_info('mame_scan_MAME_ROMs() ROM dir OP {}'.format(ROM_path_FN.getOriginalPath()))
    log_info('mame_scan_MAME_ROMs() ROM dir  P {}'.format(ROM_path_FN.getPath()))

    if options_dic['scan_CHDs']:
        CHD_path_FN = FileName(cfg.settings['chd_path'])
        log_info('mame_scan_MAME_ROMs() CHD dir OP {}'.format(CHD_path_FN.getOriginalPath()))
        log_info('mame_scan_MAME_ROMs() CHD dir  P {}'.format(CHD_path_FN.getPath()))
    else:
        CHD_path_FN = FileName('')
        log_info('Scan of CHDs disabled.')

    if options_dic['scan_Samples']:
        Samples_path_FN = FileName(cfg.settings['samples_path'])
        log_info('mame_scan_MAME_ROMs() Samples OP {}'.format(Samples_path_FN.getOriginalPath()))
        log_info('mame_scan_MAME_ROMs() Samples P  {}'.format(Samples_path_FN.getPath()))
    else:
        Samples_path_FN = FileName('')
        log_info('Scan of Samples disabled.')

    # --- Create auxiliary databases ---
    pDialog = KodiProgressDialog()
    pDialog.startProgress('Creating auxiliary databases...', 3)
    ROM_ZIP_list = mame_get_ROM_ZIP_list(machine_archives_dic)
    pDialog.updateProgressInc()
    Sample_ZIP_list = mame_get_Sample_ZIP_list(machine_archives_dic)
    pDialog.updateProgressInc()
    CHD_list = mame_get_CHD_list(machine_archives_dic)
    pDialog.endProgress()

    # --- Create a cache of files ---
    # utils_file_cache_add_dir() creates a set with all files in a given directory.
    # That set is stored in a function internal cache associated with the path.
    # Files in the cache can be searched with misc_search_file_cache()
    # utils_file_cache_add_dir() accepts invalid/empty paths, just do not add them to the cache.
    ROM_path_str = ROM_path_FN.getPath()
    CHD_path_str = CHD_path_FN.getPath()
    Samples_path_str = Samples_path_FN.getPath()
    STUFF_PATH_LIST = [ROM_path_str, CHD_path_str, Samples_path_str]
    pDialog.startProgress('Listing files in ROM/CHD/Samples directories...', len(STUFF_PATH_LIST))
    utils_file_cache_clear()
    for asset_dir in STUFF_PATH_LIST:
        pDialog.updateProgressInc()
        utils_file_cache_add_dir(asset_dir)
    pDialog.endProgress()

    # --- Scan machine archives ---
    # Traverses all machines and scans if all required files exist.
    scan_march_ROM_total = 0
    scan_march_ROM_have = 0
    scan_march_ROM_missing = 0
    scan_march_SAM_total = 0
    scan_march_SAM_have = 0
    scan_march_SAM_missing = 0
    scan_march_CHD_total = 0
    scan_march_CHD_have = 0
    scan_march_CHD_missing = 0
    r_full_list = []
    r_have_list = []
    r_miss_list = []
    dial_line = 'Scanning MAME machine archives (ROMs, CHDs and Samples)...'
    pDialog.startProgress(dial_line, len(renderdb))
    for key in sorted(renderdb):
        pDialog.updateProgressInc()

        # --- Initialise machine ---
        # log_info('mame_scan_MAME_ROMs() Checking machine {}'.format(key))
        if renderdb[key]['isDevice']: continue # Skip Devices
        m_have_str_list = []
        m_miss_str_list = []

        # --- ROMs ---
        rom_list = machine_archives_dic[key]['ROMs']
        if rom_list:
            scan_march_ROM_total += 1
            have_rom_list = [False] * len(rom_list)
            for i, rom in enumerate(rom_list):
                # --- Old code ---
                # archive_name = rom + '.zip'
                # ROM_FN = ROM_path_FN.pjoin(archive_name)
                # if ROM_FN.exists():
                # --- New code using file cache ---
                ROM_FN = utils_file_cache_search(ROM_path_str, rom, MAME_ROM_EXTS)
                if ROM_FN:
                    have_rom_list[i] = True
                    m_have_str_list.append('HAVE ROM {}'.format(rom))
                else:
                    m_miss_str_list.append('MISS ROM {}'.format(rom))
            if all(have_rom_list):
                # --- All ZIP files required to run this machine exist ---
                scan_march_ROM_have += 1
                ROM_flag = 'R'
            else:
                scan_march_ROM_missing += 1
                ROM_flag = 'r'
        else:
            ROM_flag = '-'
        db_set_ROM_flag(assetdb[key], ROM_flag)

        # --- Samples ---
        sample_list = machine_archives_dic[key]['Samples']
        if sample_list and options_dic['scan_Samples']:
            scan_march_SAM_total += 1
            have_sample_list = [False] * len(sample_list)
            for i, sample in enumerate(sample_list):
                Sample_FN = utils_file_cache_search(Samples_path_str, sample, MAME_SAMPLE_EXTS)
                if ROM_FN:
                    have_sample_list[i] = True
                    m_have_str_list.append('HAVE SAM {}'.format(sample))
                else:
                    m_miss_str_list.append('MISS SAM {}'.format(sample))
            if all(have_sample_list):
                scan_march_SAM_have += 1
                Sample_flag = 'S'
            else:
                scan_march_SAM_missing += 1
                Sample_flag = 's'
        elif sample_list and not options_dic['scan_Samples']:
            scan_march_SAM_total += 1
            scan_march_SAM_missing += 1
            Sample_flag = 's'
        else:
            Sample_flag = '-'
        db_set_Sample_flag(assetdb[key], Sample_flag)

        # --- Disks ---
        # Machines with CHDs: 2spicy, sfiii2
        chd_list = machine_archives_dic[key]['CHDs']
        if chd_list and options_dic['scan_CHDs']:
            scan_march_CHD_total += 1
            has_chd_list = [False] * len(chd_list)
            for idx, chd_name in enumerate(chd_list):
                # --- Old code ---
                # CHD_FN = CHD_path_FN.pjoin(chd_name)
                # if CHD_FN.exists():
                # --- New code using file cache ---
                # log_debug('Testing CHD "{}"'.format(chd_name))
                CHD_FN = utils_file_cache_search(CHD_path_str, chd_name, MAME_CHD_EXTS)
                if CHD_FN:
                    has_chd_list[idx] = True
                    m_have_str_list.append('HAVE CHD {}'.format(chd_name))
                else:
                    m_miss_str_list.append('MISS CHD {}'.format(chd_name))
            if all(has_chd_list):
                scan_march_CHD_have += 1
                CHD_flag = 'C'
            else:
                scan_march_CHD_missing += 1
                CHD_flag = 'c'
        elif chd_list and not options_dic['scan_CHDs']:
            scan_march_CHD_total += 1
            scan_march_CHD_missing += 1
            CHD_flag = 'c'
        else:
            CHD_flag = '-'
        db_set_CHD_flag(assetdb[key], CHD_flag)

        # Build FULL, HAVE and MISSING reports.
        r_full_list.append('Machine {} "{}"'.format(key, renderdb[key]['description']))
        if renderdb[key]['cloneof']:
            cloneof = renderdb[key]['cloneof']
            r_full_list.append('cloneof {} "{}"'.format(cloneof, renderdb[cloneof]['description']))
        if not rom_list and not sample_list and not chd_list:
            r_full_list.append('Machine has no ROMs, Samples and/or CHDs')
        else:
            r_full_list.extend(m_have_str_list)
            r_full_list.extend(m_miss_str_list)
        r_full_list.append('')

        # In the HAVE report include machines if and only if every required file is there.
        if m_have_str_list and not m_miss_str_list:
            r_have_list.append('Machine {} "{}"'.format(key, renderdb[key]['description']))
            if renderdb[key]['cloneof']:
                cloneof = renderdb[key]['cloneof']
                r_have_list.append('cloneof {} "{}"'.format(cloneof, renderdb[cloneof]['description']))
            r_have_list.extend(m_have_str_list)
            r_have_list.extend(m_miss_str_list)
            r_have_list.append('')

        # In the MISSING report include machines if anything is missing.
        if m_miss_str_list:
            r_miss_list.append('Machine {} "{}"'.format(key, renderdb[key]['description']))
            if renderdb[key]['cloneof']:
                cloneof = renderdb[key]['cloneof']
                r_miss_list.append('cloneof {} "{}"'.format(cloneof, renderdb[cloneof]['description']))
            r_miss_list.extend(m_have_str_list)
            r_miss_list.extend(m_miss_str_list)
            r_miss_list.append('')
    pDialog.endProgress()

    # Write MAME scanner reports
    reports_total = 3
    pDialog.startProgress('Saving scanner reports...', reports_total)
    log_info('Writing report "{}"'.format(cfg.REPORT_MAME_SCAN_MACHINE_ARCH_FULL_PATH.getPath()))
    report_slist = [
        '*** Advanced MAME Launcher MAME machines scanner report ***',
        'This report shows all the scanned MAME machines.',
        '',
        'MAME ROM path     "{}"'.format(ROM_path_str),
        'MAME Samples path "{}"'.format(Samples_path_str),
        'MAME CHD path     "{}"'.format(CHD_path_str),
        '',
    ]
    report_slist.extend(r_full_list)
    utils_write_slist_to_file(cfg.REPORT_MAME_SCAN_MACHINE_ARCH_FULL_PATH.getPath(), report_slist)

    pDialog.updateProgress(1)
    log_info('Writing report "{}"'.format(cfg.REPORT_MAME_SCAN_MACHINE_ARCH_HAVE_PATH.getPath()))
    report_slist = [
        '*** Advanced MAME Launcher MAME machines scanner report ***',
        'This reports shows MAME machines that have all the required',
        'ROM ZIP files, Sample ZIP files and CHD files.',
        'Machines that no require files are not listed.',
        '',
        'MAME ROM path     "{}"'.format(ROM_path_str),
        'MAME Samples path "{}"'.format(Samples_path_str),
        'MAME CHD path     "{}"'.format(CHD_path_str),
        '',
    ]
    if not r_have_list:
        r_have_list.append('Ouch!!! You do not have any ROM ZIP files and/or CHDs.')
    report_slist.extend(r_have_list)
    utils_write_slist_to_file(cfg.REPORT_MAME_SCAN_MACHINE_ARCH_HAVE_PATH.getPath(), report_slist)

    pDialog.updateProgress(2)
    log_info('Writing report "{}"'.format(cfg.REPORT_MAME_SCAN_MACHINE_ARCH_MISS_PATH.getPath()))
    report_slist = [
        '*** Advanced MAME Launcher MAME machines scanner report ***',
        'This reports shows MAME machines that miss all or some of the required',
        'ROM ZIP files, Sample ZIP files or CHD files.',
        'Machines that no require files are not listed.',
        '',
        'MAME ROM path     "{}"'.format(ROM_path_str),
        'MAME Samples path "{}"'.format(Samples_path_str),
        'MAME CHD path     "{}"'.format(CHD_path_str),
        '',
    ]
    if not r_miss_list:
        r_miss_list.append('Congratulations!!! You have no missing ROM ZIP and/or CHDs files.')
    report_slist.extend(r_miss_list)
    utils_write_slist_to_file(cfg.REPORT_MAME_SCAN_MACHINE_ARCH_MISS_PATH.getPath(), report_slist)
    pDialog.endProgress()

    # --- ROM ZIP file list ---
    scan_ROM_ZIP_files_total = 0
    scan_ROM_ZIP_files_have = 0
    scan_ROM_ZIP_files_missing = 0
    r_list = [
        '*** Advanced MAME Launcher MAME machines scanner report ***',
        'This report shows all missing MAME machine ROM ZIP files.',
        'Each missing ROM ZIP appears only once, but more than one machine may be affected.',
        '',
        'MAME ROM path     "{}"'.format(ROM_path_str),
        'MAME Samples path "{}"'.format(Samples_path_str),
        'MAME CHD path     "{}"'.format(CHD_path_str),
        '',
    ]
    pDialog.startProgress('Scanning MAME ROM ZIPs...', len(ROM_ZIP_list))
    for rom_name in ROM_ZIP_list:
        pDialog.updateProgressInc()
        scan_ROM_ZIP_files_total += 1
        ROM_FN = utils_file_cache_search(ROM_path_str, rom_name, MAME_ROM_EXTS)
        if ROM_FN:
            scan_ROM_ZIP_files_have += 1
        else:
            scan_ROM_ZIP_files_missing += 1
            r_list.append('Missing ROM {}'.format(rom_name))
    pDialog.endProgress()
    log_info('Writing report "{}"'.format(cfg.REPORT_MAME_SCAN_ROM_LIST_MISS_PATH.getPath()))
    if scan_ROM_ZIP_files_missing == 0:
        r_list.append('Congratulations!!! You have no missing ROM ZIP files.')
    utils_write_slist_to_file(cfg.REPORT_MAME_SCAN_ROM_LIST_MISS_PATH.getPath(), r_list)

    # --- Sample ZIP file list ---
    scan_Samples_ZIP_total = 0
    scan_Samples_ZIP_have = 0
    scan_Samples_ZIP_missing = 0
    r_list = [
        '*** Advanced MAME Launcher MAME machines scanner report ***',
        'This report shows all missing MAME machine Sample ZIP files.',
        'Each missing Sample ZIP appears only once, but more than one machine may be affected.',
        '',
        'MAME ROM path     "{}"'.format(ROM_path_str),
        'MAME Samples path "{}"'.format(Samples_path_str),
        'MAME CHD path     "{}"'.format(CHD_path_str),
        '',
    ]
    pDialog.startProgress('Scanning MAME Sample ZIPs...', len(Sample_ZIP_list))
    for sample_name in Sample_ZIP_list:
        pDialog.updateProgressInc()
        scan_Samples_ZIP_total += 1
        Sample_FN = utils_file_cache_search(Samples_path_str, sample_name, MAME_SAMPLE_EXTS)
        if Sample_FN:
            scan_Samples_ZIP_have += 1
        else:
            scan_Samples_ZIP_missing += 1
            r_list.append('Missing Sample {}'.format(sample_name))
    pDialog.endProgress()
    log_info('Writing report "{}"'.format(cfg.REPORT_MAME_SCAN_SAM_LIST_MISS_PATH.getPath()))
    if scan_Samples_ZIP_missing == 0:
        r_list.append('Congratulations!!! You have no missing Sample ZIP files.')
    utils_write_slist_to_file(cfg.REPORT_MAME_SCAN_SAM_LIST_MISS_PATH.getPath(), r_list)

    # --- CHD file list ---
    scan_CHD_files_total = 0
    scan_CHD_files_have = 0
    scan_CHD_files_missing = 0
    r_list = [
        '*** Advanced MAME Launcher MAME machines scanner report ***',
        'This report shows all missing MAME machine CHDs',
        'Each missing CHD appears only once, but more than one machine may be affected.',
        '',
        'MAME ROM path     "{}"'.format(ROM_path_str),
        'MAME Samples path "{}"'.format(Samples_path_str),
        'MAME CHD path     "{}"'.format(CHD_path_str),
        '',
    ]
    pDialog.startProgress('Scanning MAME CHDs...', len(CHD_list))
    for chd_name in CHD_list:
        pDialog.updateProgressInc()
        scan_CHD_files_total += 1
        CHD_FN = utils_file_cache_search(CHD_path_str, chd_name, MAME_CHD_EXTS)
        if CHD_FN:
            scan_CHD_files_have += 1
        else:
            scan_CHD_files_missing += 1
            r_list.append('Missing CHD {}'.format(chd_name))
    pDialog.endProgress()
    log_info('Writing report "{}"'.format(cfg.REPORT_MAME_SCAN_CHD_LIST_MISS_PATH.getPath()))
    if scan_CHD_files_missing == 0:
        r_list.append('Congratulations!!! You have no missing CHD files.')
    utils_write_slist_to_file(cfg.REPORT_MAME_SCAN_CHD_LIST_MISS_PATH.getPath(), r_list)

    # --- Update statistics ---
    db_safe_edit(control_dic, 'scan_machine_archives_ROM_total', scan_march_ROM_total)
    db_safe_edit(control_dic, 'scan_machine_archives_ROM_have', scan_march_ROM_have)
    db_safe_edit(control_dic, 'scan_machine_archives_ROM_missing', scan_march_ROM_missing)
    db_safe_edit(control_dic, 'scan_machine_archives_Samples_total', scan_march_SAM_total)
    db_safe_edit(control_dic, 'scan_machine_archives_Samples_have', scan_march_SAM_have)
    db_safe_edit(control_dic, 'scan_machine_archives_Samples_missing', scan_march_SAM_missing)
    db_safe_edit(control_dic, 'scan_machine_archives_CHD_total', scan_march_CHD_total)
    db_safe_edit(control_dic, 'scan_machine_archives_CHD_have', scan_march_CHD_have)
    db_safe_edit(control_dic, 'scan_machine_archives_CHD_missing', scan_march_CHD_missing)

    db_safe_edit(control_dic, 'scan_ROM_ZIP_files_total', scan_ROM_ZIP_files_total)
    db_safe_edit(control_dic, 'scan_ROM_ZIP_files_have', scan_ROM_ZIP_files_have)
    db_safe_edit(control_dic, 'scan_ROM_ZIP_files_missing', scan_ROM_ZIP_files_missing)
    db_safe_edit(control_dic, 'scan_Samples_ZIP_total', scan_Samples_ZIP_total)
    db_safe_edit(control_dic, 'scan_Samples_ZIP_have', scan_Samples_ZIP_have)
    db_safe_edit(control_dic, 'scan_Samples_ZIP_missing', scan_Samples_ZIP_missing)
    db_safe_edit(control_dic, 'scan_CHD_files_total', scan_CHD_files_total)
    db_safe_edit(control_dic, 'scan_CHD_files_have', scan_CHD_files_have)
    db_safe_edit(control_dic, 'scan_CHD_files_missing', scan_CHD_files_missing)

    # --- Scanner timestamp ---
    db_safe_edit(control_dic, 't_MAME_ROMs_scan', time.time())

    # --- Save databases ---
    db_files = [
        [control_dic, 'Control dictionary', cfg.MAIN_CONTROL_PATH.getPath()],
        [assetdb, 'MAME machine assets', cfg.ASSET_DB_PATH.getPath()],
    ]
    db_save_files(db_files)

#
# Checks for errors before scanning for SL assets.
# Caller function displays a Kodi dialog if an error is found and scanning must be aborted.
#
def mame_check_before_scan_MAME_assets(cfg, st_dic, control_dic):
    kodi_reset_status(st_dic)

    # Get assets directory. Abort if not configured/found.
    if not cfg.settings['assets_path']:
        kodi_set_error_status(st_dic, 'MAME asset directory not configured. Aborting.')
        return
    Asset_path_FN = FileName(cfg.settings['assets_path'])
    if not Asset_path_FN.isdir():
        kodi_set_error_status(st_dic, 'MAME asset directory does not exist. Aborting.')
        return

#
# Note that MAME is able to use clone artwork from parent machines. Mr. Do's Artwork ZIP files
# are provided only for parents.
# First pass: search for on-disk assets.
# Second pass: do artwork substitution
#   A) A clone may use assets from parent.
#   B) A parent may use assets from a clone.
#
def mame_scan_MAME_assets(cfg, st_dic, db_dic_in):
    control_dic = db_dic_in['control_dic']
    renderdb_dic = db_dic_in['renderdb']
    assetdb_dic = db_dic_in['assetdb']
    main_pclone_dic = db_dic_in['main_pclone_dic']

    Asset_path_FN = FileName(cfg.settings['assets_path'])
    log_info('mame_scan_MAME_assets() Asset path {}'.format(Asset_path_FN.getPath()))

    # Iterate machines, check if assets/artwork exist.
    table_str = []
    table_str.append([
        'left',
        'left', 'left', 'left', 'left', 'left', 'left', 'left',
        'left', 'left', 'left', 'left', 'left', 'left', 'left'])
    table_str.append([
        'Name',
        '3DB',  'Apr',  'Art',  'Cab',  'Clr',  'CPa',  'Fan',
        'Fly',  'Man',  'Mar',  'PCB',  'Snp',  'Tit',  'Tra'])

    # --- Create a cache of assets ---
    asset_dirs = [''] * len(ASSET_MAME_T_LIST)
    pDialog = KodiProgressDialog()
    pDialog.startProgress('Listing files in asset directories...', len(ASSET_MAME_T_LIST))
    utils_file_cache_clear()
    for i, asset_tuple in enumerate(ASSET_MAME_T_LIST):
        pDialog.updateProgressInc()
        asset_dir = asset_tuple[1]
        full_asset_dir_FN = Asset_path_FN.pjoin(asset_dir)
        asset_dir_str = full_asset_dir_FN.getPath()
        asset_dirs[i] = asset_dir_str
        utils_file_cache_add_dir(asset_dir_str)
    pDialog.endProgress()

    # --- First pass: search for on-disk assets ---
    ondisk_assets_dic = {}
    pDialog.startProgress('Scanning MAME assets/artwork (first pass)...', len(renderdb_dic))
    for m_name in sorted(renderdb_dic):
        pDialog.updateProgressInc()
        machine_assets = db_new_MAME_asset()
        for idx, asset_tuple in enumerate(ASSET_MAME_T_LIST):
            asset_key = asset_tuple[0]
            asset_dir = asset_tuple[1]
            if asset_key == 'artwork':
                asset_FN = utils_file_cache_search(asset_dirs[idx], m_name, ASSET_ARTWORK_EXTS)
            elif asset_key == 'manual':
                asset_FN = utils_file_cache_search(asset_dirs[idx], m_name, ASSET_MANUAL_EXTS)
            elif asset_key == 'trailer':
                asset_FN = utils_file_cache_search(asset_dirs[idx], m_name, ASSET_TRAILER_EXTS)
            else:
                asset_FN = utils_file_cache_search(asset_dirs[idx], m_name, ASSET_IMAGE_EXTS)
            # Low level debug.
            # if m_name == '005':
            #     log_debug('asset_key       "{}"'.format(asset_key))
            #     log_debug('asset_dir       "{}"'.format(asset_dir))
            #     log_debug('asset_dirs[idx] "{}"'.format(asset_dirs[idx]))
            #     log_debug('asset_FN        "{}"'.format(asset_FN))
            machine_assets[asset_key] = asset_FN.getOriginalPath() if asset_FN else ''
        ondisk_assets_dic[m_name] = machine_assets
    pDialog.endProgress()

    # --- Second pass: substitute artwork ---
    have_count_list = [0] * len(ASSET_MAME_T_LIST)
    alternate_count_list = [0] * len(ASSET_MAME_T_LIST)
    pDialog.startProgress('Scanning MAME assets/artwork (second pass)...', len(renderdb_dic))
    for m_name in sorted(renderdb_dic):
        pDialog.updateProgressInc()
        asset_row = ['---'] * len(ASSET_MAME_T_LIST)
        for idx, asset_tuple in enumerate(ASSET_MAME_T_LIST):
            asset_key = asset_tuple[0]
            asset_dir = asset_tuple[1]
            # Reset asset
            assetdb_dic[m_name][asset_key] = ''
            # If artwork exists on disk set it on database
            if ondisk_assets_dic[m_name][asset_key]:
                assetdb_dic[m_name][asset_key] = ondisk_assets_dic[m_name][asset_key]
                have_count_list[idx] += 1
                asset_row[idx] = 'YES'
            # If artwork does not exist on disk ...
            else:
                # if machine is a parent search in the clone list
                if m_name in main_pclone_dic:
                    for clone_key in main_pclone_dic[m_name]:
                        if ondisk_assets_dic[clone_key][asset_key]:
                            assetdb_dic[m_name][asset_key] = ondisk_assets_dic[clone_key][asset_key]
                            have_count_list[idx] += 1
                            alternate_count_list[idx] += 1
                            asset_row[idx] = 'CLO'
                            break
                # if machine is a clone search in the parent first, then search in the clones
                else:
                    # Search parent
                    parent_name = renderdb_dic[m_name]['cloneof']
                    if ondisk_assets_dic[parent_name][asset_key]:
                        assetdb_dic[m_name][asset_key] = ondisk_assets_dic[parent_name][asset_key]
                        have_count_list[idx] += 1
                        alternate_count_list[idx] += 1
                        asset_row[idx] = 'PAR'
                    # Search clones
                    else:
                        for clone_key in main_pclone_dic[parent_name]:
                            if clone_key == m_name: continue
                            if ondisk_assets_dic[clone_key][asset_key]:
                                assetdb_dic[m_name][asset_key] = ondisk_assets_dic[clone_key][asset_key]
                                have_count_list[idx] += 1
                                alternate_count_list[idx] += 1
                                asset_row[idx] = 'CLX'
                                break
        table_row = [m_name] + asset_row
        table_str.append(table_row)
    pDialog.endProgress()

    # --- Asset statistics and report ---
    total_machines = len(renderdb_dic)
    # This must match the order of ASSET_MAME_T_LIST defined in disk_IO.py
    box3D = (have_count_list[0],  total_machines - have_count_list[0],  alternate_count_list[0])
    Artp  = (have_count_list[1],  total_machines - have_count_list[1],  alternate_count_list[1])
    Art   = (have_count_list[2],  total_machines - have_count_list[2],  alternate_count_list[2])
    Cab   = (have_count_list[3],  total_machines - have_count_list[3],  alternate_count_list[3])
    Clr   = (have_count_list[4],  total_machines - have_count_list[4],  alternate_count_list[4])
    CPan  = (have_count_list[5],  total_machines - have_count_list[5],  alternate_count_list[5])
    Fan   = (have_count_list[6],  total_machines - have_count_list[6],  alternate_count_list[6])
    Fly   = (have_count_list[7],  total_machines - have_count_list[7],  alternate_count_list[7])
    Man   = (have_count_list[8],  total_machines - have_count_list[8],  alternate_count_list[8])
    Mar   = (have_count_list[9],  total_machines - have_count_list[9],  alternate_count_list[9])
    PCB   = (have_count_list[10], total_machines - have_count_list[10], alternate_count_list[10])
    Snap  = (have_count_list[11], total_machines - have_count_list[11], alternate_count_list[11])
    Tit   = (have_count_list[12], total_machines - have_count_list[12], alternate_count_list[12])
    Tra   = (have_count_list[13], total_machines - have_count_list[13], alternate_count_list[13])
    pDialog.startProgress('Creating MAME asset report...')
    report_slist = []
    report_slist.append('*** Advanced MAME Launcher MAME machines asset scanner report ***')
    report_slist.append('Total MAME machines {}'.format(total_machines))
    report_slist.append('Have 3D Boxes   {:5d} (Missing {:5d}, Alternate {:5d})'.format(*box3D))
    report_slist.append('Have Artpreview {:5d} (Missing {:5d}, Alternate {:5d})'.format(*Artp))
    report_slist.append('Have Artwork    {:5d} (Missing {:5d}, Alternate {:5d})'.format(*Art))
    report_slist.append('Have Cabinets   {:5d} (Missing {:5d}, Alternate {:5d})'.format(*Cab))
    report_slist.append('Have Clearlogos {:5d} (Missing {:5d}, Alternate {:5d})'.format(*Clr))
    report_slist.append('Have CPanels    {:5d} (Missing {:5d}, Alternate {:5d})'.format(*CPan))
    report_slist.append('Have Fanarts    {:5d} (Missing {:5d}, Alternate {:5d})'.format(*Fan))
    report_slist.append('Have Flyers     {:5d} (Missing {:5d}, Alternate {:5d})'.format(*Fly))
    report_slist.append('Have Manuals    {:5d} (Missing {:5d}, Alternate {:5d})'.format(*Man))
    report_slist.append('Have Marquees   {:5d} (Missing {:5d}, Alternate {:5d})'.format(*Mar))
    report_slist.append('Have PCBs       {:5d} (Missing {:5d}, Alternate {:5d})'.format(*PCB))
    report_slist.append('Have Snaps      {:5d} (Missing {:5d}, Alternate {:5d})'.format(*Snap))
    report_slist.append('Have Titles     {:5d} (Missing {:5d}, Alternate {:5d})'.format(*Tit))
    report_slist.append('Have Trailers   {:5d} (Missing {:5d}, Alternate {:5d})'.format(*Tra))
    report_slist.append('')
    table_str_list = text_render_table(table_str)
    report_slist.extend(table_str_list)
    log_info('Writing MAME asset report file "{}"'.format(cfg.REPORT_MAME_ASSETS_PATH.getPath()))
    utils_write_slist_to_file(cfg.REPORT_MAME_ASSETS_PATH.getPath(), report_slist)
    pDialog.endProgress()

    # Update control_dic by assigment (will be saved in caller)
    db_safe_edit(control_dic, 'assets_num_MAME_machines', total_machines)
    db_safe_edit(control_dic, 'assets_3dbox_have', box3D[0])
    db_safe_edit(control_dic, 'assets_3dbox_missing', box3D[1])
    db_safe_edit(control_dic, 'assets_3dbox_alternate', box3D[2])
    db_safe_edit(control_dic, 'assets_artpreview_have', Artp[0])
    db_safe_edit(control_dic, 'assets_artpreview_missing', Artp[1])
    db_safe_edit(control_dic, 'assets_artpreview_alternate', Artp[2])
    db_safe_edit(control_dic, 'assets_artwork_have', Art[0])
    db_safe_edit(control_dic, 'assets_artwork_missing', Art[1])
    db_safe_edit(control_dic, 'assets_artwork_alternate', Art[2])
    db_safe_edit(control_dic, 'assets_cabinets_have', Cab[0])
    db_safe_edit(control_dic, 'assets_cabinets_missing', Cab[1])
    db_safe_edit(control_dic, 'assets_cabinets_alternate', Cab[2])
    db_safe_edit(control_dic, 'assets_clearlogos_have', Clr[0])
    db_safe_edit(control_dic, 'assets_clearlogos_missing', Clr[1])
    db_safe_edit(control_dic, 'assets_clearlogos_alternate', Clr[2])
    db_safe_edit(control_dic, 'assets_cpanels_have', CPan[0])
    db_safe_edit(control_dic, 'assets_cpanels_missing', CPan[1])
    db_safe_edit(control_dic, 'assets_cpanels_alternate', CPan[2])
    db_safe_edit(control_dic, 'assets_fanarts_have', Fan[0])
    db_safe_edit(control_dic, 'assets_fanarts_missing', Fan[1])
    db_safe_edit(control_dic, 'assets_fanarts_alternate', Fan[2])
    db_safe_edit(control_dic, 'assets_flyers_have', Fly[0])
    db_safe_edit(control_dic, 'assets_flyers_missing', Fly[1])
    db_safe_edit(control_dic, 'assets_flyers_alternate', Fly[2])
    db_safe_edit(control_dic, 'assets_manuals_have', Man[0])
    db_safe_edit(control_dic, 'assets_manuals_missing', Man[1])
    db_safe_edit(control_dic, 'assets_manuals_alternate', Man[2])
    db_safe_edit(control_dic, 'assets_marquees_have', Mar[0])
    db_safe_edit(control_dic, 'assets_marquees_missing', Mar[1])
    db_safe_edit(control_dic, 'assets_marquees_alternate', Mar[2])
    db_safe_edit(control_dic, 'assets_PCBs_have', PCB[0])
    db_safe_edit(control_dic, 'assets_PCBs_missing', PCB[1])
    db_safe_edit(control_dic, 'assets_PCBs_alternate', PCB[2])
    db_safe_edit(control_dic, 'assets_snaps_have', Snap[0])
    db_safe_edit(control_dic, 'assets_snaps_missing', Snap[1])
    db_safe_edit(control_dic, 'assets_snaps_alternate', Snap[2])
    db_safe_edit(control_dic, 'assets_titles_have', Tit[0])
    db_safe_edit(control_dic, 'assets_titles_missing', Tit[1])
    db_safe_edit(control_dic, 'assets_titles_alternate', Tit[2])
    db_safe_edit(control_dic, 'assets_trailers_have', Tra[0])
    db_safe_edit(control_dic, 'assets_trailers_missing', Tra[1])
    db_safe_edit(control_dic, 'assets_trailers_alternate', Tra[2])
    db_safe_edit(control_dic, 't_MAME_assets_scan', time.time())

    # --- Save databases ---
    db_files = [
        [control_dic, 'Control dictionary', cfg.MAIN_CONTROL_PATH.getPath()],
        [assetdb_dic, 'MAME machine assets', cfg.ASSET_DB_PATH.getPath()],
    ]
    db_save_files(db_files)

# -------------------------------------------------------------------------------------------------
#
# Checks for errors before scanning for SL ROMs.
# Display a Kodi dialog if an error is found.
# Returns a dictionary of settings:
# options_dic['abort'] is always present.
# options_dic['scan_SL_CHDs'] scanning of CHDs is optional.
#
def mame_check_before_scan_SL_ROMs(cfg, st_dic, options_dic, control_dic):
    kodi_reset_status(st_dic)

    # Abort if SL are globally disabled.
    if not cfg.settings['global_enable_SL']:
        kodi_set_error_status(st_dic, 'Software Lists globally disabled. SL ROM scanning aborted.')
        return

    # Abort if SL hash path not configured.
    if not cfg.settings['SL_hash_path']:
        kodi_set_error_status(st_dic, 'Software Lists hash path not set. SL ROM scanning aborted.')
        return

    # Abort if SL ROM dir not configured.
    if not cfg.settings['SL_rom_path']:
        kodi_set_error_status(st_dic, 'Software Lists ROM path not set. SL ROM scanning aborted.')
        return

    # SL CHDs scanning is optional
    if cfg.settings['SL_chd_path']:
        SL_CHD_path_FN = FileName(cfg.settings['SL_chd_path'])
        if not SL_CHD_path_FN.isdir():
            kodi_dialog_OK('SL CHD directory does not exist. SL CHD scanning disabled.')
            options_dic['scan_SL_CHDs'] = False
        else:
            options_dic['scan_SL_CHDs'] = True
    else:
        kodi_dialog_OK('SL CHD directory not configured. SL CHD scanning disabled.')
        options_dic['scan_SL_CHDs'] = False

# Saves SL JSON databases, MAIN_CONTROL_PATH.
def mame_scan_SL_ROMs(cfg, st_dic, options_dic, SL_dic):
    log_info('mame_scan_SL_ROMs() Starting...')
    control_dic = SL_dic['control_dic']
    SL_index_dic = SL_dic['SL_index']

    # Paths have been verified at this point
    SL_hash_dir_FN = cfg.SL_DB_DIR
    log_info('mame_scan_SL_ROMs() SL hash dir OP {}'.format(SL_hash_dir_FN.getOriginalPath()))
    log_info('mame_scan_SL_ROMs() SL hash dir  P {}'.format(SL_hash_dir_FN.getPath()))

    SL_ROM_dir_FN = FileName(cfg.settings['SL_rom_path'])
    log_info('mame_scan_SL_ROMs() SL ROM dir OP {}'.format(SL_ROM_dir_FN.getOriginalPath()))
    log_info('mame_scan_SL_ROMs() SL ROM dir  P {}'.format(SL_ROM_dir_FN.getPath()))

    if options_dic['scan_SL_CHDs']:
        SL_CHD_path_FN = FileName(cfg.settings['SL_chd_path'])
        log_info('mame_scan_SL_ROMs() SL CHD dir OP {}'.format(SL_CHD_path_FN.getOriginalPath()))
        log_info('mame_scan_SL_ROMs() SL CHD dir  P {}'.format(SL_CHD_path_FN.getPath()))
    else:
        SL_CHD_path_FN = FileName('')
        log_info('Scan of SL CHDs disabled.')

    # --- Add files to cache ---
    SL_ROM_path_str = SL_ROM_dir_FN.getPath()
    SL_CHD_path_str = SL_CHD_path_FN.getPath()
    pDialog = KodiProgressDialog()
    d_text = 'Listing Sofware Lists ROM ZIPs and CHDs...'
    pDialog.startProgress('{}\n{}'.format(d_text, 'Listing SL ROM ZIP path'), 2)
    utils_file_cache_clear()
    utils_file_cache_add_dir(SL_ROM_path_str, verbose = True)
    pDialog.updateProgress(1, '{}\n{}'.format(d_text, 'Listing SL CHD path'))
    utils_file_cache_add_dir(SL_CHD_path_str, verbose = True)
    pDialog.endProgress()

    # --- SL ROM ZIP archives and CHDs ---
    # Traverse the Software Lists, check if ROMs ZIPs and CHDs exists for every SL item,
    # update and save database.
    SL_ROMs_have = 0
    SL_ROMs_missing = 0
    SL_ROMs_total = 0
    SL_CHDs_have = 0
    SL_CHDs_missing = 0
    SL_CHDs_total = 0
    r_all_list = []
    r_have_list = []
    r_miss_list = []
    d_text = 'Scanning Sofware Lists ROM ZIPs and CHDs...'
    pDialog.startProgress(d_text, len(SL_index_dic))
    for SL_name in sorted(SL_index_dic):
        pDialog.updateProgressInc('{}\nSoftware List [COLOR orange]{}[/COLOR]'.format(d_text, SL_name))

        # Load SL databases
        SL_DB_FN = SL_hash_dir_FN.pjoin(SL_name + '_items.json')
        SL_SOFT_ARCHIVES_DB_FN = SL_hash_dir_FN.pjoin(SL_name + '_ROM_archives.json')
        sl_roms = utils_load_JSON_file(SL_DB_FN.getPath(), verbose = False)
        soft_archives = utils_load_JSON_file(SL_SOFT_ARCHIVES_DB_FN.getPath(), verbose = False)

        # Scan
        for rom_key in sorted(sl_roms):
            m_have_str_list = []
            m_miss_str_list = []
            rom = sl_roms[rom_key]

            # --- ROMs ---
            rom_list = soft_archives[rom_key]['ROMs']
            if rom_list:
                have_rom_list = [False] * len(rom_list)
                for i, rom_file in enumerate(rom_list):
                    SL_ROMs_total += 1
                    SL_ROM_FN = utils_file_cache_search(SL_ROM_path_str, rom_file, SL_ROM_EXTS)
                    if SL_ROM_FN:
                        have_rom_list[i] = True
                        m_have_str_list.append('HAVE ROM {}'.format(rom_file))
                    else:
                        m_miss_str_list.append('MISS ROM {}'.format(rom_file))
                if all(have_rom_list):
                    rom['status_ROM'] = 'R'
                    SL_ROMs_have += 1
                else:
                    rom['status_ROM'] = 'r'
                    SL_ROMs_missing += 1
            else:
                rom['status_ROM'] = '-'

            # --- Disks ---
            chd_list = soft_archives[rom_key]['CHDs']
            if chd_list:
                if options_dic['scan_SL_CHDs']:
                    SL_CHDs_total += 1
                    has_chd_list = [False] * len(chd_list)
                    for idx, chd_file in enumerate(chd_list):
                        SL_CHD_FN = utils_file_cache_search(SL_CHD_path_str, chd_file, SL_CHD_EXTS)
                        # CHD_path = SL_CHD_path_str + '/' + chd_file
                        if SL_CHD_FN:
                            has_chd_list[idx] = True
                            m_have_str_list.append('HAVE CHD {}'.format(chd_file))
                        else:
                            m_miss_str_list.append('MISS CHD {}'.format(chd_file))
                    if all(has_chd_list):
                        rom['status_CHD'] = 'C'
                        SL_CHDs_have += 1
                    else:
                        rom['status_CHD'] = 'c'
                        SL_CHDs_missing += 1
                else:
                    rom['status_CHD'] = 'c'
                    SL_CHDs_missing += 1
            else:
                rom['status_CHD'] = '-'

            # --- Build report ---
            description = sl_roms[rom_key]['description']
            clone_name = sl_roms[rom_key]['cloneof']
            r_all_list.append('SL {} item {} "{}"'.format(SL_name, rom_key, description))
            if clone_name:
                clone_description = sl_roms[clone_name]['description']
                r_all_list.append('cloneof {} "{}"'.format(clone_name, clone_description))
            if m_have_str_list:
                r_all_list.extend(m_have_str_list)
            if m_miss_str_list:
                r_all_list.extend(m_miss_str_list)
            r_all_list.append('')

            if m_have_str_list:
                r_have_list.append('SL {} item {} "{}"'.format(SL_name, rom_key, description))
                if clone_name:
                    r_have_list.append('cloneof {} "{}"'.format(clone_name, clone_description))
                r_have_list.extend(m_have_str_list)
                if m_miss_str_list: r_have_list.extend(m_miss_str_list)
                r_have_list.append('')

            if m_miss_str_list:
                r_miss_list.append('SL {} item {} "{}"'.format(SL_name, rom_key, description))
                if clone_name:
                    r_miss_list.append('cloneof {} "{}"'.format(clone_name, clone_description))
                r_miss_list.extend(m_miss_str_list)
                if m_have_str_list: r_miss_list.extend(m_have_str_list)
                r_miss_list.append('')
        # Save SL database to update flags and update progress.
        utils_write_JSON_file(SL_DB_FN.getPath(), sl_roms, verbose = False)
    pDialog.endProgress()

    # Write SL scanner reports
    reports_total = 3
    pDialog.startProgress('Writing scanner reports...', reports_total)
    log_info('Writing SL ROM ZIPs/CHDs FULL report')
    log_info('Report file "{}"'.format(cfg.REPORT_SL_SCAN_MACHINE_ARCH_FULL_PATH.getPath()))
    sl = [
        '*** Advanced MAME Launcher Software Lists scanner report ***',
        'This report shows all the scanned SL items',
        '',
    ]
    sl.extend(r_all_list)
    utils_write_slist_to_file(cfg.REPORT_SL_SCAN_MACHINE_ARCH_FULL_PATH.getPath(), sl)

    pDialog.updateProgressInc()
    log_info('Writing SL ROM ZIPs and/or CHDs HAVE report')
    log_info('Report file "{}"'.format(cfg.REPORT_SL_SCAN_MACHINE_ARCH_HAVE_PATH.getPath()))
    sl = [
        '*** Advanced MAME Launcher Software Lists scanner report ***',
        'This reports shows the SL items with ROM ZIPs and/or CHDs with HAVE status',
        '',
    ]
    if r_have_list:
        sl.extend(r_have_list)
    else:
        sl.append('You do not have any ROM ZIP or CHD files!')
    utils_write_slist_to_file(cfg.REPORT_SL_SCAN_MACHINE_ARCH_HAVE_PATH.getPath(), sl)

    pDialog.updateProgressInc()
    log_info('Writing SL ROM ZIPs/CHDs MISS report')
    log_info('Report file "{}"'.format(cfg.REPORT_SL_SCAN_MACHINE_ARCH_MISS_PATH.getPath()))
    sl = [
        '*** Advanced MAME Launcher Software Lists scanner report ***',
        'This reports shows the SL items with ROM ZIPs and/or CHDs with MISSING status',
        '',
    ]
    if r_miss_list:
        sl.extend(r_miss_list)
    else:
        sl.append('Congratulations! No missing SL ROM ZIP or CHD files.')
    utils_write_slist_to_file(cfg.REPORT_SL_SCAN_MACHINE_ARCH_MISS_PATH.getPath(), sl)
    pDialog.endProgress()

    # Update statistics, timestamp and save control_dic.
    db_safe_edit(control_dic, 'scan_SL_archives_ROM_total', SL_ROMs_total)
    db_safe_edit(control_dic, 'scan_SL_archives_ROM_have', SL_ROMs_have)
    db_safe_edit(control_dic, 'scan_SL_archives_ROM_missing', SL_ROMs_missing)
    db_safe_edit(control_dic, 'scan_SL_archives_CHD_total', SL_CHDs_total)
    db_safe_edit(control_dic, 'scan_SL_archives_CHD_have', SL_CHDs_have)
    db_safe_edit(control_dic, 'scan_SL_archives_CHD_missing', SL_CHDs_missing)
    db_safe_edit(control_dic, 't_SL_ROMs_scan', time.time())
    utils_write_JSON_file(cfg.MAIN_CONTROL_PATH.getPath(), control_dic)

#
# Checks for errors before scanning for SL assets.
# Display a Kodi dialog if an error is found and returns True if scanning must be aborted.
# Returns False if no errors.
#
def mame_check_before_scan_SL_assets(cfg, st_dic, control_dic):
    kodi_reset_status(st_dic)

    # Abort if SL are globally disabled.
    if not cfg.settings['global_enable_SL']:
        kodi_set_error_status(st_dic, 'Software Lists globally disabled. SL ROM scanning aborted.')
        return

    # Get assets directory. Abort if not configured/found.
    if not cfg.settings['assets_path']:
        kodi_set_error_status(st_dic, 'Asset directory not configured. Aborting.')
        return
    Asset_path_FN = FileName(cfg.settings['assets_path'])
    if not Asset_path_FN.isdir():
        kodi_set_error_status(st_dic, 'Asset directory does not exist. Aborting.')
        return

def mame_scan_SL_assets(cfg, st_dic, SL_dic):
    log_debug('mame_scan_SL_assets() Starting...')
    control_dic = SL_dic['control_dic']
    SL_index_dic = SL_dic['SL_index']
    SL_pclone_dic = SL_dic['SL_PClone_dic']

    # At this point assets_path is configured and the directory exists.
    Asset_path_FN = FileName(cfg.settings['assets_path'])
    log_info('mame_scan_SL_assets() SL asset path {}'.format(Asset_path_FN.getPath()))

    # --- Traverse Software List, check if ROM exists, update and save database ---
    table_str = []
    table_str.append(['left', 'left', 'left', 'left', 'left', 'left', 'left', 'left', 'left'])
    table_str.append(['Soft', 'Name', '3DB',  'Tit',  'Snap', 'Bft',  'Fan',  'Tra',  'Man'])
    have_count_list = [0] * len(ASSET_SL_T_LIST)
    alternate_count_list = [0] * len(ASSET_SL_T_LIST)
    SL_item_count = 0
    # DEBUG code
    # SL_index_dic = {
    #     "32x" :
    #     { "display_name" : "Sega 32X cartridges", "num_with_CHDs" : 0, "num_with_ROMs" : 203, "rom_DB_noext" : "32x" }
    # }
    d_text = 'Scanning Sofware Lists assets/artwork...'
    pDialog = KodiProgressDialog()
    pDialog.startProgress(d_text, len(SL_index_dic))
    for SL_name in sorted(SL_index_dic):
        pDialog.updateProgressInc('{}\nSoftware List [COLOR orange]{}[/COLOR]'.format(d_text, SL_name))

        # --- Load SL databases ---
        file_name = SL_index_dic[SL_name]['rom_DB_noext'] + '_items.json'
        SL_DB_FN = cfg.SL_DB_DIR.pjoin(file_name)
        SL_roms = utils_load_JSON_file(SL_DB_FN.getPath(), verbose = False)

        # --- Cache files ---
        utils_file_cache_clear(verbose = False)
        num_assets = len(ASSET_SL_T_LIST)
        asset_dirs = [''] * num_assets
        for i, asset_tuple in enumerate(ASSET_SL_T_LIST):
            asset_dir = asset_tuple[1]
            full_asset_dir_FN = Asset_path_FN.pjoin(asset_dir).pjoin(SL_name)
            asset_dir_str = full_asset_dir_FN.getPath()
            asset_dirs[i] = asset_dir_str
            utils_file_cache_add_dir(asset_dir_str, verbose = False)

        # --- First pass: scan for on-disk assets ---
        assets_file_name = SL_index_dic[SL_name]['rom_DB_noext'] + '_assets.json'
        SL_asset_DB_FN = cfg.SL_DB_DIR.pjoin(assets_file_name)
        # log_info('Assets JSON "{}"'.format(SL_asset_DB_FN.getPath()))
        ondisk_assets_dic = {}
        for rom_key in sorted(SL_roms):
            SL_assets = db_new_SL_asset()
            for idx, asset_tuple in enumerate(ASSET_SL_T_LIST):
                asset_key = asset_tuple[0]
                asset_dir = asset_tuple[1]
                full_asset_dir_FN = Asset_path_FN.pjoin(asset_dir).pjoin(SL_name)
                if asset_key == 'manual':
                    asset_FN = utils_file_cache_search(asset_dirs[idx], rom_key, ASSET_MANUAL_EXTS)
                elif asset_key == 'trailer':
                    asset_FN = utils_file_cache_search(asset_dirs[idx], rom_key, ASSET_TRAILER_EXTS)
                else:
                    asset_FN = utils_file_cache_search(asset_dirs[idx], rom_key, ASSET_IMAGE_EXTS)
                # log_info('Testing P "{}"'.format(asset_FN.getPath()))
                SL_assets[asset_key] = asset_FN.getOriginalPath() if asset_FN else ''
            ondisk_assets_dic[rom_key] = SL_assets

        # --- Second pass: substitute artwork ---
        main_pclone_dic = SL_pclone_dic[SL_name]
        SL_assets_dic = {}
        for rom_key in sorted(SL_roms):
            SL_item_count += 1
            SL_assets_dic[rom_key] = db_new_SL_asset()
            asset_row = ['---'] * len(ASSET_SL_T_LIST)
            for idx, asset_tuple in enumerate(ASSET_SL_T_LIST):
                asset_key = asset_tuple[0]
                asset_dir = asset_tuple[1]
                # >> Reset asset
                SL_assets_dic[rom_key][asset_key] = ''
                # TODO Refactor this to reduce indentation.
                # >> If artwork exists on disk set it on database
                if ondisk_assets_dic[rom_key][asset_key]:
                    SL_assets_dic[rom_key][asset_key] = ondisk_assets_dic[rom_key][asset_key]
                    have_count_list[idx] += 1
                    asset_row[idx] = 'YES'
                # >> If artwork does not exist on disk ...
                else:
                    # >> if machine is a parent search in the clone list
                    if rom_key in main_pclone_dic:
                        for clone_key in main_pclone_dic[rom_key]:
                            if ondisk_assets_dic[clone_key][asset_key]:
                                SL_assets_dic[rom_key][asset_key] = ondisk_assets_dic[clone_key][asset_key]
                                have_count_list[idx] += 1
                                alternate_count_list[idx] += 1
                                asset_row[idx] = 'CLO'
                                break
                    # >> if machine is a clone search in the parent first, then search in the clones
                    else:
                        # >> Search parent
                        parent_name = SL_roms[rom_key]['cloneof']
                        if ondisk_assets_dic[parent_name][asset_key]:
                            SL_assets_dic[rom_key][asset_key] = ondisk_assets_dic[parent_name][asset_key]
                            have_count_list[idx] += 1
                            alternate_count_list[idx] += 1
                            asset_row[idx] = 'PAR'
                        # >> Search clones
                        else:
                            for clone_key in main_pclone_dic[parent_name]:
                                if clone_key == rom_key: continue
                                if ondisk_assets_dic[clone_key][asset_key]:
                                    SL_assets_dic[rom_key][asset_key] = ondisk_assets_dic[clone_key][asset_key]
                                    have_count_list[idx] += 1
                                    alternate_count_list[idx] += 1
                                    asset_row[idx] = 'CLX'
                                    break
            table_row = [SL_name, rom_key] + asset_row
            table_str.append(table_row)
        # --- Write SL asset JSON ---
        utils_write_JSON_file(SL_asset_DB_FN.getPath(), SL_assets_dic, verbose = False)
    pDialog.endProgress()

    # Asset statistics and report.
    # This must match the order of ASSET_SL_T_LIST defined in disk_IO.py
    _3db = (have_count_list[0], SL_item_count - have_count_list[0], alternate_count_list[0])
    Tit  = (have_count_list[1], SL_item_count - have_count_list[1], alternate_count_list[1])
    Snap = (have_count_list[2], SL_item_count - have_count_list[2], alternate_count_list[2])
    Boxf = (have_count_list[3], SL_item_count - have_count_list[3], alternate_count_list[3])
    Fan  = (have_count_list[4], SL_item_count - have_count_list[4], alternate_count_list[4])
    Tra  = (have_count_list[5], SL_item_count - have_count_list[5], alternate_count_list[5])
    Man  = (have_count_list[6], SL_item_count - have_count_list[6], alternate_count_list[6])
    pDialog.startProgress('Creating SL asset report...')
    report_slist = []
    report_slist.append('*** Advanced MAME Launcher Software List asset scanner report ***')
    report_slist.append('Total SL items {}'.format(SL_item_count))
    report_slist.append('Have 3D Boxes  {:6d} (Missing {:6d}, Alternate {:6d})'.format(*_3db))
    report_slist.append('Have Titles    {:6d} (Missing {:6d}, Alternate {:6d})'.format(*Tit))
    report_slist.append('Have Snaps     {:6d} (Missing {:6d}, Alternate {:6d})'.format(*Snap))
    report_slist.append('Have Boxfronts {:6d} (Missing {:6d}, Alternate {:6d})'.format(*Boxf))
    report_slist.append('Have Fanarts   {:6d} (Missing {:6d}, Alternate {:6d})'.format(*Fan))
    report_slist.append('Have Trailers  {:6d} (Missing {:6d}, Alternate {:6d})'.format(*Tra))
    report_slist.append('Have Manuals   {:6d} (Missing {:6d}, Alternate {:6d})'.format(*Man))
    report_slist.append('')
    table_str_list = text_render_table(table_str)
    report_slist.extend(table_str_list)
    log_info('Writing SL asset report file "{}"'.format(cfg.REPORT_SL_ASSETS_PATH.getPath()))
    utils_write_slist_to_file(cfg.REPORT_SL_ASSETS_PATH.getPath(), report_slist)
    pDialog.endProgress()

    # Update control_dic by assigment (will be saved in caller) and save JSON.
    db_safe_edit(control_dic, 'assets_SL_num_items', SL_item_count)
    db_safe_edit(control_dic, 'assets_SL_3dbox_have', _3db[0])
    db_safe_edit(control_dic, 'assets_SL_3dbox_missing', _3db[1])
    db_safe_edit(control_dic, 'assets_SL_3dbox_alternate', _3db[2])
    db_safe_edit(control_dic, 'assets_SL_titles_have', Tit[0])
    db_safe_edit(control_dic, 'assets_SL_titles_missing', Tit[1])
    db_safe_edit(control_dic, 'assets_SL_titles_alternate', Tit[2])
    db_safe_edit(control_dic, 'assets_SL_snaps_have', Snap[0])
    db_safe_edit(control_dic, 'assets_SL_snaps_missing', Snap[1])
    db_safe_edit(control_dic, 'assets_SL_snaps_alternate', Snap[2])
    db_safe_edit(control_dic, 'assets_SL_boxfronts_have', Boxf[0])
    db_safe_edit(control_dic, 'assets_SL_boxfronts_missing', Boxf[1])
    db_safe_edit(control_dic, 'assets_SL_boxfronts_alternate', Boxf[2])
    db_safe_edit(control_dic, 'assets_SL_fanarts_have', Fan[0])
    db_safe_edit(control_dic, 'assets_SL_fanarts_missing', Fan[1])
    db_safe_edit(control_dic, 'assets_SL_fanarts_alternate', Fan[2])
    db_safe_edit(control_dic, 'assets_SL_trailers_have', Tra[0])
    db_safe_edit(control_dic, 'assets_SL_trailers_missing', Tra[1])
    db_safe_edit(control_dic, 'assets_SL_trailers_alternate', Tra[2])
    db_safe_edit(control_dic, 'assets_SL_manuals_have', Man[0])
    db_safe_edit(control_dic, 'assets_SL_manuals_missing', Man[1])
    db_safe_edit(control_dic, 'assets_SL_manuals_alternate', Man[2])
    db_safe_edit(control_dic, 't_SL_assets_scan', time.time())
    utils_write_JSON_file(cfg.MAIN_CONTROL_PATH.getPath(), control_dic)
