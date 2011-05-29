# -*- coding: iso-8859-1 -*-
#------------------------------------------------------------
# pelisalacarta - XBMC Plugin
# Lista de vídeos favoritos
# http://blog.tvalacarta.info/plugin-xbmc/pelisalacarta/
#------------------------------------------------------------
import logger
import os

'''
El formato de una ruta samba es:

smb://[usuario:password]@servidor/rutacompartida/directorio/

Ej:

Con login y password: smb://jesus:mipassword@MEDIASERVER/DESCARGAS/xbmc/favoritos
Con acceso guest: smb://MEDIASERVER/DESCARGAS/xbmc/favoritos
'''
def parse_url(url):

    logger.info("url="+url)    
    # Algunas trampas para facilitar el parseo de la url
    url = url.strip()
    if not url.endswith("/"):
        url = url + "/"
    logger.info("url="+url)    
        
    import re
    patron = 'smb\:\/\/([^\:]+)\:([^\@]+)@([^\/]+)\/([^\/]+)/(.*/)?'
    matches = re.compile(patron,re.DOTALL).findall(url)

    if len(matches)>0:
        #logger.info("url con login y password")
        server_name=matches[0][2]
        share_name=matches[0][3]
        path=matches[0][4]
        user=matches[0][0]
        password=matches[0][1]
    else:
        #logger.info("url sin login y password")
        patron = 'smb\:\/\/([^\/]+)\/([^\/]+)/(.*/)?'
        matches = re.compile(patron,re.DOTALL).findall(url)
        
        if len(matches)>0:
            server_name=matches[0][0]
            share_name=matches[0][1]
            path=matches[0][2]
            user=""
            password=""
        else:
            server_name=""
            share_name=""
            path=""
            user=""
            password=""

    if path=="":
        path="/"
    
    logger.info("server_name="+server_name)
    logger.info("share_name="+share_name)
    logger.info("path="+path)
    logger.info("user="+user)
    logger.info("password="+password)

    return server_name,share_name,path,user,password

def connect(server_name,user,password):
    import smb,nmb

    logger.info("Crea netbios...")
    netbios = nmb.NetBIOS()
    
    logger.info("Averigua IP...")
    nbhost = netbios.gethostbyname(server_name)
    server_ip = nbhost[0].get_ip()
    logger.info("server_ip="+server_ip)
    
    logger.info("Crea smb...")
    remote = smb.SMB(server_name, server_ip)
    logger.info("ok")

    if remote.is_login_required():
        logger.info("Login...")
        if user=="":
            logger.info("User vacio, se asume 'guest'")
            user="guest"    
        remote.login(user, password)
    else:
        logger.info("Login no requerido")

    return remote

'''
Graba el string "filecontent" en un fichero "filename" almacenado en la ruta samba indicada
'''
def write_file(filename,filecontent,url):

    # Separa la URL en los elementos    
    server_name,share_name,path,user,password = parse_url(url)

    # Conecta con el servidor remoto
    remote = connect(server_name,user,password)    

    # Crea un fichero temporal con el bookmark
    logger.info("Crea fichero temporal")
    try:
        import xbmc
        localfilename = xbmc.translatePath( "special://temp" )
    except:
        localfilename = config.get_data_path()
    logger.info("localfilename="+localfilename)
    
    localfilename = os.path.join(localfilename,"bookmark.tmp")
    bookmarkfile = open(localfilename,"w")
    bookmarkfile.write(filecontent)
    bookmarkfile.flush()
    bookmarkfile.close()

    # Copia el bookmark al directorio Samba
    logger.info("Crea el fichero remoto")
    bookmarkfile = open(localfilename,"rb")
    remote.stor_file(share_name, path+"/"+filename, bookmarkfile.read)
    bookmarkfile.close()

    # Borra el fichero temporal
    logger.info("Borra el fichero local")
    os.remove(localfilename)

def get_files(url):

    logger.info("get_files")
    
    # Separa la URL en los elementos    
    server_name,share_name,path,user,password = parse_url(url)

    # Conecta con el servidor remoto
    remote = connect(server_name,user,password)
    
    ficheros = []
    
    for f in remote.list_path(share_name, path + '*'):
        name = f.get_longname()
        logger.info("name="+name)
        if name == '.' or name == '..':
            continue

        if f.is_directory():
            continue

        ficheros.append(name)

    return ficheros

def get_file_handle_for_reading(filename,url):

    logger.info("get_file_handle_for_reading")
    
    # Separa la URL en los elementos    
    server_name,share_name,path,user,password = parse_url(url)

    # Conecta con el servidor remoto
    remote = connect(server_name,user,password)

    # Crea un fichero temporal con el bookmark
    logger.info("Crea fichero temporal")
    try:
        import xbmc
        localfilename = xbmc.translatePath( "special://temp" )
    except:
        localfilename = config.get_data_path()
    logger.info("localfilename="+localfilename)

    localfilename = os.path.join(localfilename,"bookmark.tmp")
    
    # Lo abre    
    bookmarkfile = open(localfilename,"wb")
    
    # Lo copia de la URL
    try:
        remote.retr_file(share_name, path + filename, bookmarkfile.write, password = password)
    finally:
        bookmarkfile.close()

    return open(localfilename)

def file_exists(filename,url):

    logger.info("file_exists "+ filename )
    
    # Separa la URL en los elementos    
    server_name,share_name,path,user,password = parse_url(url)

    # Conecta con el servidor remoto
    remote = connect(server_name,user,password)

    ficheros = []
    
    for f in remote.list_path(share_name, path + '*'):
        name = f.get_longname()
        #logger.info("name="+name)
        if name == '.' or name == '..':
            continue

        if f.is_directory():
            continue

        ficheros.append(name)

    try:
        print ficheros.index(filename)
        return True
    except:
        return False

def remove_file(filename,url):

    logger.info("remove_file "+filename)
    
    # Separa la URL en los elementos    
    server_name,share_name,path,user,password = parse_url(url)

    # Conecta con el servidor remoto
    remote = connect(server_name,user,password)
    
    remote.remove(share_name,path+filename,password=password)


def test():
    '''
    parse_url("smb://jesus:mipassword@MEDIASERVER/DESCARGAS/XBMC/favoritos")
    parse_url("smb://MEDIASERVER/DESCARGAS/XBMC/favoritos")
    parse_url("smb://MEDIASERVER/DESCARGAS")
    parse_url("smb://jesus:mipassword@MEDIASERVER/DESCARGAS")

    write_file("bookmark.txt","aqui ira el bookmark","smb://MEDIASERVER/DESCARGAS/xbmc/favoritos")
    ficheros = get_files("smb://MEDIASERVER/DESCARGAS/XBMC/favoritos")
    
    for fichero in ficheros:
        handle = get_file_handle_for_reading(fichero,"smb://MEDIASERVER/DESCARGAS/XBMC/favoritos")
        data = handle.read()
        handle.close()
        print data
    '''
    
    print file_exists("00000005.txt","smb://MEDIASERVER/DESCARGAS/XBMC/favoritos")
    print file_exists("00000001.txt","smb://MEDIASERVER/DESCARGAS/XBMC/favoritos")

if __name__ == "__main__":
    test()
    