# -*- coding: utf-8 -*-
# Copyright 2017 Laura Klünder
# See https://github.com/codingcatgirl/ttml2srt
#
# MIT License
#
# Copyright (c) 2017 Laura Klünder
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import re
import io
from datetime import timedelta
from defusedxml import ElementTree as ET

def ttml2srt( infile, outfile ):
	tree = ET.parse( infile )
	root = tree.getroot()

	# strip namespaces
	for elem in root.getiterator():
		elem.tag = elem.tag.split('}', 1)[-1]
		elem.attrib = {name.split('}', 1)
					[-1]: value for name, value in elem.attrib.items()}

	# get styles
	styles = {}
	for elem in root.findall('./head/styling/style'):
		style = {}
		if 'color' in elem.attrib:
			color = elem.attrib['color']
			if color not in ('#FFFFFF', '#000000'):
				style['color'] = color
		if 'fontStyle' in elem.attrib:
			fontstyle = elem.attrib['fontStyle']
			if fontstyle in ('italic', ):
				style['fontstyle'] = fontstyle
		styles[elem.attrib['id']] = style

	body = root.find('./body')

	# parse correct start and end times
	def parse_time_expression(expression, default_offset=timedelta(0)):
		offset_time = re.match(r'^([0-9]+(\.[0-9]+)?)(h|m|s|ms|f|t)$', expression)
		if offset_time:
			time_value, _, metric = offset_time.groups()
			time_value = float(time_value)
			if metric == 'h':
				return default_offset + timedelta(hours=time_value)
			elif metric == 'm':
				return default_offset + timedelta(minutes=time_value)
			elif metric == 's':
				return default_offset + timedelta(seconds=time_value)
			elif metric == 'ms':
				return default_offset + timedelta(milliseconds=time_value)
			elif metric == 'f':
				raise NotImplementedError(
					'Parsing time expressions by frame is not supported!')
			elif metric == 't':
				raise NotImplementedError(
					'Parsing time expressions by ticks is not supported!')

		clock_time = re.match(
			r'^([0-9]{2,}):([0-9]{2,}):([0-9]{2,}(\.[0-9]+)?)$', expression)
		if clock_time:
			hours, minutes, seconds, _ = clock_time.groups()
			return timedelta(hours=int(hours), minutes=int(minutes), seconds=float(seconds))

		clock_time_frames = re.match(
			r'^([0-9]{2,}):([0-9]{2,}):([0-9]{2,}):([0-9]{2,}(\.[0-9]+)?)$', expression)
		if clock_time_frames:
			raise NotImplementedError(
				'Parsing time expressions by frame is not supported!')

		raise ValueError('unknown time expression: %s' % expression)


	def parse_times(elem, default_begin=timedelta(0)):
		if 'begin' in elem.attrib:
			begin = parse_time_expression(
				elem.attrib['begin'], default_offset=default_begin)
		else:
			begin = default_begin
		elem.attrib['{abs}begin'] = begin

		end = None
		if 'end' in elem.attrib:
			end = parse_time_expression(
				elem.attrib['end'], default_offset=default_begin)

		dur = None
		if 'dur' in elem.attrib:
			dur = parse_time_expression(elem.attrib['dur'])

		if dur is not None:
			if end is None:
				end = begin + dur
			else:
				end = min(end, begin + dur)

		elem.attrib['{abs}end'] = end

		for child in elem:
			parse_times(child, default_begin=begin)


	parse_times(body)

	timestamps = set()
	for elem in body.findall('.//*[@{abs}begin]'):
		timestamps.add(elem.attrib['{abs}begin'])

	for elem in body.findall('.//*[@{abs}end]'):
		timestamps.add(elem.attrib['{abs}end'])

	timestamps.discard(None)

	# render subtitles on each timestamp


	def render_subtitles(elem, timestamp, parent_style=None):

		if timestamp < elem.attrib['{abs}begin']:
			return ''
		if elem.attrib['{abs}end'] is not None and timestamp >= elem.attrib['{abs}end']:
			return ''

		result = ''

		style = parent_style.copy() if parent_style is not None else {}
		if 'style' in elem.attrib:
			style.update(styles[elem.attrib['style']])

		if 'color' in style:
			result += '<font color="%s">' % style['color']

		if style.get('fontstyle') == 'italic':
			result += '<i>'

		if elem.text:
			result += elem.text.strip()
		if len(elem):
			for child in elem:
				result += render_subtitles(child, timestamp)
				if child.tail:
					result += child.tail.strip()

		if 'color' in style:
			result += '</font>'

		if style.get('fontstyle') == 'italic':
			result += '</i>'

		if elem.tag in ('div', 'p', 'br'):
			result += '\n'

		return result


	rendered = []
	for timestamp in sorted(timestamps):
		rendered.append((timestamp, re.sub(r'\n\n\n+', '\n\n',
										render_subtitles(body, timestamp)).strip()))

	if not rendered:
		exit(0)

	# group timestamps together if nothing changes
	rendered_grouped = []
	last_text = None
	for timestamp, content in rendered:
		if content != last_text:
			rendered_grouped.append((timestamp, content))
		last_text = content

	# output srt
	rendered_grouped.append((rendered_grouped[-1][0] + timedelta(hours=24), ''))


	def format_timestamp(timestamp):
		return ('%02d:%02d:%02.3f' % (timestamp.total_seconds() // 3600,
									timestamp.total_seconds() // 60 % 60,
									timestamp.total_seconds() % 60)).replace('.', ',')


	if isinstance( outfile, str ) or isinstance( outfile, unicode ):
		file = io.open( outfile, 'w', encoding='utf-8' )
	else:
		file = outfile

	srt_i = 1
	for i, (timestamp, content) in enumerate(rendered_grouped[:-1]):
		if content == '':
			continue
		file.write( bytearray( '%d\n' % srt_i, 'utf-8' ) )
		file.write( bytearray(
			format_timestamp( timestamp ) +
			' --> ' +
			format_timestamp( rendered_grouped[i + 1][0] ) +
			'\n'
		) )
		file.write( bytearray( content + '\n\n', 'utf-8' ) )
		srt_i += 1
	file.close()
