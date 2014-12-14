import resources.lib.rtlxl

rtlxl = resources.lib.rtlxl.RtlXL()

print rtlxl.get_overzicht()

print '\n\n'

print rtlxl.get_categories('http://www.rtl.nl/system/s4m/ipadfd/d=ipad/fmt=adaptive/ak=260801/')

print '\n\n'

print rtlxl.get_items('http://www.rtl.nl/system/s4m/ipadfd/d=ipad/fmt=adaptive/ak=260801/', True, False)

print rtlxl.get_items('http://www.rtl.nl/system/s4m/ipadfd/d=ipad/fmt=adaptive/ak=260801/', False, False)

print rtlxl.get_items('http://www.rtl.nl/system/s4m/ipadfd/d=ipad/fmt=adaptive/ak=260801/', True, True)

print rtlxl.get_items('http://www.rtl.nl/system/s4m/ipadfd/d=ipad/fmt=adaptive/ak=260801/', False, True)
