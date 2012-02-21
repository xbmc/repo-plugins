# coding=utf-8
#
# <BestRussianTV plugin for XBMC>
# Copyright (C) <2011>  <BestRussianTV>
#
#       This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
ContentType = ''
class ItemPaging:
    itemsOnPage = '0'
    pageNumber = '0'
    totalItems = '0'
    totalPages = '0'
    def get(self):
        req = ''
        if self.itemsOnPage == '0' and self.pageNumber == '0' and self.totalItems == '0' and self.totalPages == '0':
            req = '<d4p1:paging xmlns:d5p1="http://schemas.datacontract.org/2004/07/IVS.Common" i:nil="true" />'
        else:
            req = '<d4p1:paging xmlns:d5p1="http://schemas.datacontract.org/2004/07/IVS.Common">'
            self.itemsOnPage = '<d5p1:itemsOnPage>' + self.itemsOnPage + '</d5p1:itemsOnPage>'
            self.pageNumber = '<d5p1:pageNumber>' + self.pageNumber + '</d5p1:pageNumber>'
            self.totalItems = '<d5p1:totalItems>' + self.totalItems + '</d5p1:totalItems>'
            self.totalPages = '<d5p1:totalPages>' + self.totalPages + '</d5p1:totalPages>'
            req = req + self.itemsOnPage + self.pageNumber + self.totalItems + self.totalPages + '</d4p1:paging>'
        return req
    
     
    
    
    