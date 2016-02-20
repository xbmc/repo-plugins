from xbmcswift2 import Plugin, xbmcgui
from resources.lib import cook
import pyxbmct.addonwindow as pyxbmct

plugin = Plugin()

SITE_URL = 'http://www.taste.com.au/' 


@plugin.route('/')
def main_menu():
    """ main menu """
    item = [
        {
            'label': plugin.get_string(30000),
            'path': plugin.url_for('search_first_page', page_num=1),
            'thumbnail': 'https://our.umbraco.org/media/wiki/113820/635312684468394660_Searchpng.png',
            'properties': {'fanart_image': 'http://media4.popsugar-assets.com/files/2013/07/22/987/n/28443503/b0de91cc2eb79060_shutterstock_130928207.xxxlarge/i/Prep-Produce-Advance.jpg'}
        },
        {
            'label': plugin.get_string(30001),
            'path': plugin.url_for('recipe_collection', keyword='Highly rated'),
            'thumbnail': 'http://www.medicarehelp.org/wp-content/uploads/2013/11/rating.jpg',
            'properties': {'fanart_image': 'http://myfrenchcookingtour.com/wp-content/uploads/2014/05/cooking-time.jpg'}
        },
        {
            'label': plugin.get_string(30002),
            'path': plugin.url_for('recipe_collection', keyword='Just added'),
            'thumbnail': 'http://www.mogulmusic.com/images/just_added.gif',
            'properties': {'fanart_image': 'http://www.cooksmarts.com/wp-content/uploads/2015/09/Landing-Page-Cooking-Guides-Jess-Kitchen-Chopping-1060x650.jpg'}
        },
        {
            
            'label': plugin.get_string(30003),
            'path': plugin.url_for('recipe_collection', keyword='Most searched for'),
            'thumbnail': 'https://our.umbraco.org/media/wiki/113820/635312684468394660_Searchpng.png',
            'properties': {'fanart_image': 'https://lh3.googleusercontent.com/45vm1IkVheRAvy7ujXee2qYPovXOCLkXRbMqELXIcv7XmAVfnmU31NbT4i-sRvUk3X1c=h900'}
        },
        {
            'label': plugin.get_string(30004),
            'path': plugin.url_for('recipe_collection', keyword='Random recipe'),
            'thumbnail': 'http://cdn.macheesmo.com/wp-content/themes/macheesmo2014/assets/images/random-recipe.png',
            'properties': {'fanart_image': 'http://www.colonelsretreat.com/home/system/special_slider/cooking.png'}
        }
    ]

    return item


@plugin.route('/search/<page_num>', name='search_first_page')
@plugin.route('/search/<page_num>/<search_keyword>')
def search(page_num, search_keyword=""):
    """ search the recipe collection """
    if not search_keyword:
        search_keyword = plugin.keyboard(default=None, heading='Search Recipes', hidden=False)
        search_keyword = search_keyword.replace(' ', '+')

    url = 'http://www.taste.com.au/search-recipes/?q=' + search_keyword + '&page=' + str(page_num)
    result = cook.get_search(url)
    
    next_page = 1
    next_page = int(page_num) + 1

    item = []
    for i in result:
        item.append({
            'label': i['label'],
            'path': plugin.url_for('get_recipe', url=i['path']),
            'thumbnail': i['thumbnail'],
            'properties': {'fanart_image': i['thumbnail'] }
        })

    item.append({
        'label': 'NEXT PAGE',
        'path': plugin.url_for('search', page_num = next_page, search_keyword=search_keyword),
    })
    
    return item


@plugin.route('/recipe/<url>/')
def get_recipe(url):
    METHOD_NAME = 'METHOD: '
    INGRED_NAME = 'INGREDIENTS: '

    item = cook.get_recipe(url)
    
    # Fetch recipe info from website with scraper
    for i in item:
        title = i['title']
        sub_title = i['sub_title']
        
        if not sub_title:
            sub_title = i['title']
        
        prep_time = i['prep_time']
        cook_time = i['cook_time']
        ing = i['ing']
        diff = i['diff']
        serv = i['serv']
        image = i['img']
        star = i['star']
        source = i['source']
    
    # Fetch method steps from website with scraper
    method_steps = []
    method = cook.get_recipe_method(url)
    for i in method:
        method_steps.append({
            'step': i['step'],
    })
    
    # Fetch ingredients from website with scraper
    ingred_list = [] 
    ingred = cook.get_recipe_ingred(url)
    for i in ingred:
        ingred_list.append({
            'ingred': i['ing'],
    })
    
    # Run GUI classes
    window = RecipeWindow(title)
    window.set_sub_title(sub_title)
    window.set_recipe_info(prep_time, cook_time, ing, diff, serv, star, source)
    window.set_image(image)
    window.set_ingred(INGRED_NAME, ingred_list)
    window.set_method(METHOD_NAME, method_steps)
    window.doModal()
    del window


@plugin.route('/recipe_collection/<keyword>')
def recipe_collection(keyword):
    
    result = cook.get_highest_rated('http://www.taste.com.au/menus/', keyword)
    print 'here!!!!!!!'
    print result
    item = []
    for i in result:
        item.append({
            'label': i['label'],
            'path': plugin.url_for('get_recipe', url=i['path'])
        })
    
    return item


class RecipeWindow(pyxbmct.AddonDialogWindow):

    def __init__(self, title=''):
        super(RecipeWindow, self).__init__(title)
        self.setGeometry(1280, 720, 9, 4)
        # connenct a key action (Backspace) to close window.
        self.connect(pyxbmct.ACTION_NAV_BACK, self.close)

    def set_sub_title(self, sub_title):
        # recipe sub title
        label = pyxbmct.Label(sub_title, alignment=pyxbmct.ALIGN_JUSTIFY)
        self.placeControl(label, 0, 0, columnspan = 4)

    def set_recipe_info(self, prep_time, cook_time, ing, diff, serv, star, source):
        # Prep time label
        self.label = pyxbmct.Label('Prep Time: ')
        self.placeControl(self.label, 0.7, 3)
        #
        self.label = pyxbmct.Label(prep_time, textColor='0xff808080')
        self.placeControl(self.label, 0.7, 3.4) 
        # Cook time label
        self.label = pyxbmct.Label('Cook Time: ')
        self.placeControl(self.label, 1.1, 3)
        #
        self.label = pyxbmct.Label(cook_time, textColor='0xff808080')
        self.placeControl(self.label, 1.1, 3.4)
        # Ingred label
        self.label = pyxbmct.Label('Ingredients: ')
        self.placeControl(self.label, 1.5, 3)   
        # 
        self.label = pyxbmct.Label(ing, textColor='0xff808080')
        self.placeControl(self.label, 1.5, 3.4)
        # Diff label
        self.label = pyxbmct.Label('Difficulty: ')
        self.placeControl(self.label, 1.9, 3)
        #
        self.label = pyxbmct.Label(diff, textColor='0xff808080')
        self.placeControl(self.label, 1.9, 3.4)
        # Serve label
        self.label = pyxbmct.Label('Serves: ')
        self.placeControl(self.label, 2.3, 3)
        #
        self.label = pyxbmct.Label(serv, textColor='0xff808080')
        self.placeControl(self.label, 2.3, 3.4)
        # Star Rating label 
        self.label = pyxbmct.Label('Stars: ')
        self.placeControl(self.label, 2.7, 3)
        # 
        self.label = pyxbmct.Label(star, textColor='0xff808080')
        self.placeControl(self.label, 2.7, 3.4)
        # Source label
        self.label = pyxbmct.Label('Source: ')
        self.placeControl(self.label, 3.1, 3)
        # 
        self.label = pyxbmct.Label(source, textColor='0xff808080')
        self.placeControl(self.label, 3.1, 3.4)
 
    def set_method(self, METHOD_NAME, method_steps):
        # List
        list_label = pyxbmct.Label(METHOD_NAME)
        self.placeControl(list_label, 4, 1.65)
        #
        self.list_item_label = pyxbmct.TextBox()
        self.placeControl(self.list_item_label, 4.5, 1.95, 4, 2)
        # List
        self.list = pyxbmct.List()
        self.placeControl(self.list, 4.5, 1.4, 5, 0.6)
        # Add items to the list
        step_num = 1
        for i in method_steps:
            items = ['{0}.  '.format(step_num) + i['step']] 
            self.list.addItems(items)
            step_num = step_num + 1
            
        # Connect the list to a function to display which list is selected
        self.connect(self.list, lambda: xbmc.executebuiltin('Notification(Note!,{0} selected.)'.format(
            self.list.getListItem(self.list.getSelectedPosition()).getLabel())))
        # Connect key and mouse events for the list navaigation feedback
        self.connectEventList(
            [pyxbmct.ACTION_MOVE_DOWN,
             pyxbmct.ACTION_MOVE_UP,
             pyxbmct.ACTION_MOUSE_WHEEL_DOWN,
             pyxbmct.ACTION_MOUSE_WHEEL_UP,
             pyxbmct.ACTION_MOUSE_MOVE],  
             self.list_update)
    
    def set_ingred(self, INGRED_NAME, ingred_list):
        # Label for ingredients
        self.label = pyxbmct.Label(INGRED_NAME)
        self.placeControl(self.label, .6, 0)
        # List of ingredients
        self.list = pyxbmct.List()
        self.placeControl(self.list, 1, 0, 8, 2)
        # Add items to the list
        step_num = 1
        for i in ingred_list:
            items = ['- ' + i['ingred'] ]
            self.list.addItems(items)
            step_num = step_num + 1
    
    def list_update(self):
        try:
            if self.getFocus() == self.list:
                self.list_item_label.setText(self.list.getListItem(self.list.getSelectedPosition()).getLabel())
            else:
                self.list_item_label.setText('')
        except (RuntimeError, SystemError):
            pass

    def set_image(self, img):
        # img
        self.img = img
        self.image = pyxbmct.Image(self.img)
        self.placeControl(self.image, 0.8, 1.95, 3, 1)

# For side window recipe info when browsing recipes
class SideWindow(pyxbmct.AddonDialogWindow):

    def __init__(self, title=''):
        super(SideWindow, self).__init__(title)
        self.setGeometry(200, 300, 5, 2)
        


if __name__ == '__main__':
    plugin.run()
