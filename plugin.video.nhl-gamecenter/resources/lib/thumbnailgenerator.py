import os
import urllib

#Check if Python Image Library is available
try:
    from PIL import Image
except:
    try:
        from pil import Image
    except:
        print "PIL not available"

#URLs
logos = {"CHI":"http://1.cdn.nhle.com/blackhawks/images/logos/extralarge.png",
         "CMB":"http://1.cdn.nhle.com/bluejackets/images/logos/extralarge.png",
         "DET":"http://1.cdn.nhle.com/redwings/images/logos/extralarge.png",
         "NSH":"http://1.cdn.nhle.com/predators/images/logos/extralarge.png",
         "STL":"http://1.cdn.nhle.com/blues/images/logos/extralarge.png",
         "NJD":"http://1.cdn.nhle.com/devils/images/logos/extralarge.png",
         "NYI":"http://1.cdn.nhle.com/islanders/images/logos/extralarge.png",
         "NYR":"http://1.cdn.nhle.com/rangers/images/logos/extralarge.png",
         "PHI":"http://1.cdn.nhle.com/flyers/images/logos/extralarge.png",
         "PIT":"http://1.cdn.nhle.com/penguins/images/logos/extralarge.png",
         "CGY":"http://1.cdn.nhle.com/flames/images/logos/extralarge.png",
         "COL":"http://1.cdn.nhle.com/avalanche/images/logos/extralarge.png",
         "EDM":"http://1.cdn.nhle.com/oilers/images/logos/extralarge.png",
         "MIN":"http://1.cdn.nhle.com/wild/images/logos/extralarge.png",
         "VAN":"http://1.cdn.nhle.com/canucks/images/logos/extralarge.png",
         "BOS":"http://1.cdn.nhle.com/bruins/images/logos/extralarge.png",
         "BUF":"http://1.cdn.nhle.com/sabres/images/logos/extralarge.png",
         "MON":"http://1.cdn.nhle.com/canadiens/images/logos/extralarge.png",
         "OTT":"http://1.cdn.nhle.com/senators/images/logos/extralarge.png",
         "TOR":"http://1.cdn.nhle.com/mapleleafs/images/logos/extralarge.png",
         "ANA":"http://1.cdn.nhle.com/ducks/images/logos/extralarge.png",
         "DAL":"http://1.cdn.nhle.com/stars/images/logos/extralarge.png",
         "LOS":"http://1.cdn.nhle.com/kings/images/logos/extralarge.png",
         "PHX":"http://1.cdn.nhle.com/coyotes/images/logos/extralarge.png",
         "SAN":"http://1.cdn.nhle.com/sharks/images/logos/extralarge.png",
         "CAR":"http://1.cdn.nhle.com/hurricanes/images/logos/extralarge.png",
         "FLA":"http://1.cdn.nhle.com/panthers/images/logos/extralarge.png",
         "TAM":"http://1.cdn.nhle.com/lightning/images/logos/extralarge.png",
         "WSH":"http://1.cdn.nhle.com/capitals/images/logos/extralarge.png",
         "WPG":"http://1.cdn.nhle.com/jets/images/logos/extralarge.png",
         "ATL":"http://1.cdn.nhle.com/thrashers/images/logos/extralarge.png",
         "ARI":"http://1.cdn.nhle.com/coyotes/images/logos/extralarge.png"}

def deleteThumbnails(ROOTDIR):
    #Delete old images
    print "Deleting old thumbnails..."
        
    folders = ["images/cover_black",
               "images/cover_transparent",
               "images/cover_ice",
               "images/square_black",
               "images/square_transparent",
               "images/square_ice",
               "images/169_black",
               "images/169_transparent",
               "images/169_ice",
               "images/logos"]
    
    for folder in folders:        
        for the_file in os.listdir(os.path.join(ROOTDIR, folder)):
            file_path = os.path.join(os.path.join(ROOTDIR, folder), the_file)
            try:
                if os.path.isfile(file_path):
                    os.unlink(file_path)
            except Exception, e:
                print e
 
    print "Old thumbnails deleted"

def createThumbnails(ROOTDIR, ADDON_PATH_PROFILE, imgtype, color):       
    #Download all logos
    try:
        for logo in logos.keys():
            open(os.path.join(ADDON_PATH_PROFILE, "images/logos/" + logo + ".png"))

        print "Logos found"
    except IOError:
        print "Downloading logos..."
        
        if not os.path.exists(os.path.join(ADDON_PATH_PROFILE, "images/logos/")):
            os.makedirs(os.path.join(ADDON_PATH_PROFILE, "images/logos/"))
        
        for logo in logos.keys():
            #Download the logo
            url = logos[logo]
            image = urllib.URLopener()
            image.retrieve(url,os.path.join(ADDON_PATH_PROFILE, "images/logos/" + logo + ".png"))
            
        print "Logos downloaded"
    

    #Generate thumbnail for each match
    print "Generating thumbnails..."
    
    if not os.path.exists(os.path.join(ADDON_PATH_PROFILE, "images/" + imgtype + "_" + color + "/")):
        os.makedirs(os.path.join(ADDON_PATH_PROFILE, "images/" + imgtype + "_" + color + "/"))
        
    for logo in logos.keys():
        blank_image = Image.open(os.path.join(ROOTDIR, "resources/images/blank_" + imgtype + "_" + color + ".png"))
        home_image = Image.open(os.path.join(ADDON_PATH_PROFILE, "images/logos/" + logo + ".png"))

        for awaylogo in logos.keys():

            if awaylogo == logo:
                continue
        
            away_image = Image.open(os.path.join(ADDON_PATH_PROFILE, "images/logos/" + awaylogo + ".png"))
            game_image = os.path.join(ADDON_PATH_PROFILE, "images/" + imgtype + "_" + color + "/" + awaylogo + "vs" + logo + ".png")

            if imgtype == "cover":
                blank_image.paste(away_image, (28,74), away_image)
                blank_image.paste(home_image, (28,210), home_image)
                blank_image.save(game_image)
            elif imgtype == "square":        
                blank_image.paste(away_image, (28,21), away_image)
                blank_image.paste(home_image, (28,135), home_image)
                blank_image.save(game_image)
            elif imgtype == "169":        
                blank_image.paste(away_image, (128,21), away_image)
                blank_image.paste(home_image, (128,135), home_image)
                blank_image.save(game_image)

    print "Thumbnails generated"
