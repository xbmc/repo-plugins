import resources.lib.rtlxl

rtlxl = resources.lib.rtlxl.RtlXL()

print rtlxl.get_overzicht()

print '\n\n'

print rtlxl.get_categories('http://www.rtl.nl/system/s4m/vfd/version=2/fun=abstract/d=pc/fmt=smooth/ak=340348/output=json/pg=1/')

print '\n\n'

print rtlxl.get_items('http://www.rtl.nl/system/s4m/vfd/version=2/fun=abstract/d=pc/fmt=smooth/ak=340348/output=json/pg=1/', True, 'adaptive')

print rtlxl.get_items('http://www.rtl.nl/system/s4m/vfd/version=2/fun=abstract/d=pc/fmt=smooth/ak=340348/output=json/pg=1/', False, 'adaptive')

print rtlxl.get_items('http://www.rtl.nl/system/s4m/vfd/version=2/fun=abstract/d=pc/fmt=smooth/ak=340348/output=json/pg=1/', True, 'progressive')

print rtlxl.get_items('http://www.rtl.nl/system/s4m/vfd/version=2/fun=abstract/d=pc/fmt=smooth/ak=340348/output=json/pg=1/', False, 'smooth')
