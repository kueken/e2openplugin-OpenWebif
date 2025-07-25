# -*- coding: utf-8 -*-

##########################################################################
# OpenWebif: FileController
##########################################################################
# Copyright (C) 2011 - 2020 E2OpenPlugins
#
# This program is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software Foundation,
# Inc., 51 Franklin Street, Fifth Floor, Boston MA 02110-1301, USA.
##########################################################################

import os
from re import match
from glob import glob
from six.moves.urllib.parse import quote
import json
import six

from twisted.web import static, resource, http

from Components.config import config
from Tools.Directories import fileExists
from Plugins.Extensions.OpenWebif.controllers.utilities import lenient_force_utf_8, sanitise_filename_slashes, getUrlArg


def new_getRequestHostname(self):
	host = self.getHeader(b'host')
	if host:
		if host[0] == '[':
			return host.split(']', 1)[0] + "]"
		return host.split(':', 1)[0].encode('ascii')
	return self.getHost().host.encode('ascii')

# Do wee need this?
#http.Request.getRequestHostname = new_getRequestHostname


class FileController(resource.Resource):
	def render(self, request):
		action = getUrlArg(request, "action", "download")
		file = getUrlArg(request, "file")

		if file is not None:
			filename = lenient_force_utf_8(file)
			filename = sanitise_filename_slashes(os.path.realpath(filename))

			if not os.path.exists(filename):
				return "File '%s' not found" % (filename)

			if action == "stream":
				name = getUrlArg(request, "name", "stream")
				port = config.OpenWebif.port.value
				proto = 'http'
				if request.isSecure():
					port = config.OpenWebif.https_port.value
					proto = 'https'
				ourhost = request.getHeader('host')
				m = match(r'.+\:(\d+)$', ourhost)
				if m is not None:
					port = html.escape(m.group(1))

				from html import escape
				from html import escape as html_escape
				escaped_name = escape(name)
				escaped_hostname = escape(request.getRequestHostname().decode('ascii'))
				response = "#EXTM3U\n#EXTVLCOPT:http-reconnect=true\n#EXTINF:-1,%s\n%s://%s:%s/file?action=download&file=%s" % (escaped_name, proto, escaped_hostname, port, quote(filename))
				request.setHeader("Content-Disposition", 'attachment;filename="%s.m3u"' % escaped_name)
				request.setHeader("Content-Type", "application/x-mpegurl")
				return response
			elif action == "delete":
				request.setResponseCode(http.OK)
				return "TODO: DELETE FILE: %s" % (filename)
			elif action == "download":
				request.setHeader("Content-Disposition", "attachment;filename=\"%s\"" % (filename.split('/')[-1]))
				rfile = static.File(six.ensure_binary(filename), defaultType="application/octet-stream")
				return rfile.render(request)
			else:
				return "wrong action parameter"

		path = getUrlArg(request, "dir")
		if path is not None:
			pattern = '*'
			nofiles = False
			pattern = getUrlArg(request, "pattern", "*")
			nofiles = getUrlArg(request, "nofiles") is not None
			directories = []
			files = []
			request.setHeader("content-type", "application/json; charset=utf-8")
			if fileExists(path):
				if path == '/':
					path = ''
				try:
					files = glob.glob(path + '/' + pattern)
				except:  # nosec # noqa: E722
					files = []
				files.sort()
				tmpfiles = files[:]
				for x in tmpfiles:
					if os.path.isdir(x):
						directories.append(x + '/')
						files.remove(x)
				if nofiles:
					files = []
				return six.ensure_binary(json.dumps({"result": True, "dirs": directories, "files": files}, indent=2))
			else:
				return six.ensure_binary(json.dumps({"result": False, "message": "path %s not exits" % (path)}, indent=2))
