#!/usr/bin/python
# -*- coding: utf-8 -*-

import logging
import logging.config
import os
import ConfigParser
import smtplib
import socket
from smtplib import SMTP
from logging.config import fileConfig
from xml.etree import ElementTree as ET

if not os.path.exists('OutputXML'):
        os.makedirs('OutputXML')

if not os.path.exists('Log'):
        os.makedirs('Log')
        os.makedirs('Log/CustomerLog')
        os.makedirs('Log/MainLog')
        os.makedirs('Log/ProgramerLog')

try:
    ParseError = ET.ParseError
except ImportError:
    from xml.parsers import expat
    ParseError = expat.ExpatError

config = ConfigParser.ConfigParser()


#dohvacanje postavki logera
try:
    logging.config.fileConfig('./Config/Log/log.ini')
    logP = logging.getLogger("programer")
    logC = logging.getLogger("customer")
except IOError as message:
    print message
    exit()
except NameError as message:
    print message
    exit()

try:
    config.readfp(open(r'./Config/XMLdocument/xml_path.txt'))
    config.readfp(open(r'./Config/Mail/mail_server.txt'))
except ConfigParser.ParsingError as message:
    logC.error('Configuration problem ' +str(message))
    logP.error('Configuration problem ' +str(message))
    exit()
except IOError as message:
    logC.error(message)
    logP.error(message)
    exit()

#Dohvačanje konfiguracijske putanje i vrijednosti
try:
    input_xml = config.get('documents path', 'input_xml_path')
    output_xml = config.get('documents path', 'output_xml_path')
    model_path = config.get('model path', 'model_path')
    port = config.get('smtp', 'port')
    smtp_server = config.get('smtp', 'smtp_server')
    sender = config.get('mail', 'sender')
    receiver= config.get('mail', 'receiver')
except ConfigParser.NoOptionError as message:
    logC.error('Configuration problem ' +str(message))
    logP.error('Configuration problem ' +str(message))
except ConfigParser.NoSectionError as message:
    logC.error('Configuration problem ' +str(message))
    logP.error('Configuration problem ' +str(message))

def getRoot(tag):
    #dohvaćamo model
    model_tree = ET.parse(model_path+'/'+tag+'.xml')
    model_root = model_tree.getroot()
    return model_root , model_tree

def deleteKey(root_atribute,difference):
    #briše dobivene tagove
    del root_atribute[difference]
    return root_atribute

def deleteSubelementTags(model_tag,model_attribute,root):
    #dobiva tagove subelemenata modela i prolazi kroz input xml, ukoliko se tagovi podudaraju, uspoređuje ih i šalje razliku na deleteKey
    for root_sub_element in root:
        if root_sub_element.tag == model_tag:
            sub_element_diff = set(root_sub_element.attrib)-set(model_attribute)
            if len(sub_element_diff) > 0:
                logC.info('TAG ' + model_tag + ' differences ' + str(sub_element_diff))
                for difference in sub_element_diff:
                    deleteKey(root_sub_element.attrib,difference)
                    

                    

def correctSubelementTags(model_root,root):
    #šalje se svaki tag modela na usporedbu u deleteSubelementTags
    try:
        for model_tag in model_root:
            deleteSubelementTags(model_tag.tag,model_tag.attrib,root)
    except:
        logC.info(root.tag + ' does not have children tags to correct ')
        pass
    
        
def correctRootTags(model_root,root):
    #trazimo raliku u rootTagu modela i inputa. Ukoliko postoje saljemo na deletekey
    root_tag_diff = set(root.attrib)-set(model_root.attrib)
    if len(root_tag_diff) > 0:
        logC.info(root.tag + ' START TAG delete ' + str(root_tag_diff))
        for tag in root_tag_diff:
            new_start_tag = deleteKey(root.attrib,tag)
        return new_start_tag
    else:
        logC.info(root.tag +' START TAG no differences ')
        return root
    
        
def findUnimportantSubelements(input_xmlTree,model_xmlTree):
    #trazimo da li razlike u subelementima postoje 
    elemListInput = []
    elemListModel = []
    for elem in input_xmlTree.iter():
        elemListInput.append(elem.tag)
    for elem in model_xmlTree.iter():
        elemListModel.append(elem.tag)
    value = set(elemListInput)-set(elemListModel)
    return value

def removeSubelementTag(unimportant_subelement):
    #prolazimo kroz dobivene razlike i brišemo ih na input xmlu
    for subelement in unimportant_subelement:
        for element in root.iter():
            for child in list(element):
                if child.tag == subelement:
                    element.remove(child)

def removeFile(fullname):
    #brišemo dobiveni file
    os.remove(fullname)

def sendMail(msg):
    #slanje mailova
    try:
        smtpObj = smtplib.SMTP(smtp_server,port)
        smtpObj.sendmail(sender, receiver, msg)         
    except NameError as message:
        logC.error('Cannot send mail '+str(message))
        logP.error('Cannot send mail '+str(message))
    except TypeError as message:
        logC.error('Problem sending mail ' +str(message))
        logP.error('Problem sending mail ' +str(message))
    except socket.gaierror as message :
        logC.error('Problem sending mail ' +str(message))
        logP.error('Problem sending mail ' +str(message))
    except smtplib.SMTPException as message:
        logC.error(message)
        logP.error(message)



try:
    if not os.listdir(input_xml):
    #provjera da li postoje input dokumenti
        msg = "Input XML directory is empty"
        logC.warning(msg)
        logP.warning(msg)
        try:
            sendMail(msg)
        except TypeError as message:
            logC.error('Problem sending mail ' +str(message))
            logP.error('Problem sending mail ' +str(message))
except OSError as message:
    logC.error(message)
    logP.error(message)
    exit()
    


for filename in os.listdir(input_xml):
    #uzimamo jedan po jedan input dokument
    if not filename.endswith('.xml'):
        continue
    fullname = os.path.join(input_xml, filename)
    try:
        tree = ET.parse(fullname)
        root = tree.getroot()
    except ParseError as message:
        logC.error('ParseError ' +fullname+ ',' +str(message) )
        logP.error('ParseError ' +fullname+ ',' +str(message) )
        continue
    try:
        model_root , model_tree = getRoot(root.tag)
        #dohvača se model po tagu input xmla
    except IOError:
        msg = ('IOError model ' +root.tag+ ' not exists ')
        logC.error(msg)
        logP.error(msg)
        sendMail(msg)
        continue 
        #ukoliko model nije napravljen, ne postoji
    except ParseError as message:
        logC.error('ParseError model ' +root.tag+ ',' +str(message) )
        logP.error('ParseError model ' +root.tag+ ',' +str(message) )
        continue  

        
    unimportant_subelement = findUnimportantSubelements(tree,model_tree)
        #tražimo razlike u subelementima inputa i modela

    if len(unimportant_subelement) > 0:
        logC.info(root.tag + ' CHILDREN TAGS delete ' + str(unimportant_subelement))
        removeSubelementTag(unimportant_subelement)
            #pozivamo ukoliko postoje razlike u subelementima 
    else:
        logC.info(root.tag + ' CHILDREN TAGS  no differences ')
        

    if len(root.attrib) > 0:
            #provjerava da li startni root tag ima tagova
        new_root_tag = correctRootTags(model_root,root)
    else:
        logC.info(root.tag +' START TAG dont exists ')


    new_Subemelement_tags = correctSubelementTags(model_root,root)
        #pozivamo funkciju za izbacivanje tagova subelemenata
    try:
        tree.write(output_xml+'/'+root.tag+'.xml')
    except IOError as message:
        logC.error(message)
        logP.error(message)
    except NameError as message:
        logC.error(message)
        logP.error(message)
        #radimo novi tree nakon korekcije

    logC.info('Delete Input Xml ' + fullname)
    logC.info('############# ')
    #removeFile(fullname)
    