#!/usr/bin/env python
#
# Copyright (c) 2010-2011 Appcelerator, Inc. All Rights Reserved.
# Licensed under the Apache Public License (version 2)
#
# parse out Titanium API documentation templates into a 
# format that can be used by other documentation generators
# such as PDF, etc.

import os, sys, traceback
import re, optparse
import generators
from common import lazyproperty, dict_has_non_empty_member, not_real_titanium_types

try:
	import yaml
except:
	print >> sys.stderr, "You don't have pyyaml!\n"
	print >> sys.stderr, "You can install it with:\n"
	print >> sys.stderr, ">  sudo easy_install pyyaml\n"
	print >> sys.stderr, ""
	sys.exit(1)

this_dir = os.path.dirname(os.path.abspath(__file__))

# We package mako already in support/android/mako.
android_support_dir = os.path.abspath(os.path.join(this_dir, "..", "support", "android"))
sys.path.append(android_support_dir)
from mako.template import Template

# TiLogger is also in support/android
from tilogger import *
log = None

# We package the python markdown module already in /support/module/support/markdown.
module_support_dir = os.path.abspath(os.path.join(this_dir, "..", "support", "module", "support"))
sys.path.append(module_support_dir)
import markdown

DEFAULT_PLATFORMS = ["android", "iphone", "ipad"]
DEFAULT_SINCE = "0.8"
apis = {} # raw conversion from yaml
annotated_apis = {} # made friendlier for templates, etc.
current_api = None
<<<<<<< HEAD

stats = {
	'modules':0,
	'objects':0,
	'properties':0,
	'methods':0
}

default_language = "javascript"

def to_ordered_dict(orig_dict, key_order):
	if not use_ordered_dict:
		return orig_dict
	already_added = []
	odict = OrderedDict()
	for key in key_order:
		if key in orig_dict:
			odict[key] = orig_dict[key]
			already_added.append(key)

	# Possible that not all keys were provided, so go thru orig
	# dict and make sure all elements get in new, ordered dict
	for key in orig_dict:
		if not key in already_added:
			odict[key] = orig_dict[key]
	return odict

def strip_tags(value):
	return re.sub(r'<[^>]*?>', '', value)

def namesort(a,b):
	return cmp(a['name'],b['name'])

def map_properties(srcobj, destobj, srcprops, destprops):
	for i in range(len(srcprops)):
		srcprop = srcprops[i]
		destprop = destprops[i]
		destobj[destprop] = srcobj[srcprop]
	return destobj

def resolve_supported_platforms(parent_platforms, object_specs):
	platforms = [x.lower() for x in parent_platforms]
	for p in parent_platforms:
		if '-'+p.lower() in object_specs and p.lower() in platforms:
			platforms.remove(p.lower())
	return platforms

def clean_type(the_type):
	type_out = the_type.replace('`', '')
	type_out = type_out.replace('|', ',') # settle on one of two of the valid type separators
	type_out = ','.join( [s.strip() for s in type_out.split(',') if len(s)] )
	m = re.search(r'(href.*>|tt>)+(.*)\<', type_out)
	if m and len(m.groups()) == 2:
		type_out = m.groups()[1]
	type_out = type_out[0].upper() + type_out[1:]
#	type_out = string.capwords(type_out, '.')
	type_out = '<'.join( [ s[0].upper() + s[1:] for s in type_out.split('<') if len(s) ])
	type_out = ','.join( [ s[0].upper() + s[1:] for s in type_out.split(',') if len(s) ])
	if ',' in type_out:
		type_out = ','.join( [ clean_type(s) for s in type_out.split(',') if len(s) ] )
	if '.' in type_out:
		type_out = '.'.join( [ clean_type(s) for s in type_out.split('.') if len(s) ] )
	if type_out.lower() in ['int','integer','float','double','long']:
		type_out = 'Number'
	if type_out.lower() == 'bool':
		type_out = 'Boolean'
	if type_out.lower() == 'domnode': # special case
		type_out = 'DOMNode'
	if type_out[0].isdigit():
		type_out = '_' + type_out # this handles 2DMatrix and 3DMatrix, which are invalid JS names
	return type_out

def clean_namespace(ns_in):
	def clean_part(part):
		if len(part) and part[0].isdigit():
			return '_' + part
		else:
			return part
	return '.'.join( [ clean_part(s) for s in ns_in.split('.') ])

def to_jsca_example(example):
	return map_properties(example, {}, ('description', 'code'), ('name', 'code'))

def to_jsca_property(prop):
	result = map_properties(prop, {}, ('name', 'type_jsca', 'value', 'isClassProperty'), ('name', 'type', 'description', 'isClassProperty'))
	if result['type']:
		result['type'] = clean_type(result['type'])
	result['isInstanceProperty'] = not result['isClassProperty']
	result['since'] = [ { 'name': 'Titanium Mobile SDK', 'version' : prop['since'] } ]
	result['userAgents'] = [ { 'platform' : x } for x in prop['platforms'] ]
	result['isInternal'] = False # we don't make this distinction (yet anyway)
	result['examples'] = [] # we don't have examples at the property level (yet anyway)
	return to_ordered_dict(result, ('name',)) 

def to_jsca_param(param):
	result = map_properties(param, {}, ('name', 'description'), ('name', 'description'))
	if param['type']:
		result['type'] = clean_type(param['type'])
	# we don't have data for this yet in our tdocs:
	result['usage'] = ''
	return to_ordered_dict(result, ('name',))

def to_jsca_function(method):
	result = map_properties(method, {}, ('name', 'value'), ('name', 'description'))
	if method['returntype'] and method['returntype'].lower() != 'void':
		result['returnTypes'] = [ { 'type': clean_type(method['returntype']), 'description' : '' }]
	if method['parameters']:
		result['parameters'] = [to_jsca_param(x) for x in method['parameters']]
	result['since'] = [ { 'name': 'Titanium Mobile SDK', 'version' : method['since'] } ]
	result['userAgents'] = [ { 'platform' : x } for x in method['platforms'] ]
	result['isInstanceProperty'] = True # we don't have class static methods
	result['isClassProperty'] = False # we don't have class static methods
	result['isInternal'] = False # we don't make this distinction (yet anyway)
	result['examples'] = [] # we don't have examples at the method level (yet anyway)
	result['references'] = [] # we don't use the notion of 'references' (yet anyway)
	result['exceptions'] = [] # we don't specify exceptions (yet anyway)
	result['isConstructor'] = False # we don't expose native class constructors
	result['isMethod'] = True # all of our functions are class instance functions, ergo methods
	return to_ordered_dict(result, ('name',))

def to_jsca_event(event):
	result = map_properties(event, {}, ('name', 'value'), ('name', 'description'))
	result['properties'] = []
	if event['properties']:
		for key in event['properties']:
			result['properties'].append( { 'name': key, 'description': event['properties'][key] } )
	return to_ordered_dict(result, ('name',))

def apisort(a,b):
	return cmp(a.namespace,b.namespace)

htmlr = re.compile(r'<.*?>')
def remove_html_tags(data):
    return htmlr.sub('', data)

class API(object):
	def remove_html_tags(self,str):
		return remove_html_tags(str)
	def vsdoc_return_type(self, str):
		retTypes = {
			'bool' : 'true',
			'boolean' : 'true',
			'void' : '',
			'string' : "''",
			'double' : '0.0',
			'int' : '0',
			'array' : '[]',
			'object' : '{}',
			'function' : 'function(){}',
			'float' : '0.0',
			'float,string' : "[0.0,'']",
			'int,string' : "[0,'']",
			'string,int' : "['',0]",
			'date, int' : '[new Date(),0]',
			'int, string' : "[0, '']",
			'date' : 'new Date()',
			'long' : '0',
			'callback' : 'function(){}',
			'Intent' : 'Titanium.Android.Intent',
			'Titanium.App.Android.R':"{}",
			'Number, String': '[Number, String]'
		}
		return retTypes.get(str,str)
	
	def __init__(self,name):
		self.namespace = name
		self.description = None
		self.typestr = None
		self.subtype = None
		self.returns = None
		self.methods = []
		self.properties = []
		self.events = []
		self.examples = []
		self.platforms = []
		self.since = '0.8'
		self.deprecated = None
		self.parameters = []
		self.notes = None
		self.objects = []
		self.parent_namespace = ".".join(self.namespace.split('.')[0:-1])
	
	def build_search_index(self):
		index = []
		index.append(self.namespace)	
		index.append(" ".join(self.namespace.split('.')))
		index.append(self.description)
		for o in self.events:
			index.append(o['name'])
		for o in self.methods:
			index.append(o['name'])
		for o in self.properties:
			index.append(o['name'])
		for o in self.examples:
			index.append(strip_tags(o['description']))
		if self.notes!=None:
			index.append(strip_tags(self.notes))
		return remove_html_tags(" ".join(index))	
	def add_object(self,obj):
		if obj.typestr!='proxy': 
			tokens = obj.namespace.split(".")
			m = 'create%s' % tokens[len(tokens)-1]
			tokens[len(tokens)-1] = m
			link = '<a href="%s.html">%s</a>'%(obj.namespace,obj.namespace)
			self.add_method(m,'create and return an instance of %s' %link,'object')
			self.add_method_property(m,'parameters','object','(optional) a dictionary object properties defined in %s'%link)
		if obj.typestr == 'proxy':
			obj.typestr = 'object'
		self.objects.append(obj)
		self.objects.sort(apisort)
	def set_description(self,desc):
		self.description = desc
	def set_since(self,since):
		self.since = since
	def set_deprecated(self,version,note):
		self.deprecated = {'version':version,'reason':note}
	def add_common_proxy_methods(self):
		# these are common module methods
		self.add_method('fireEvent','fire a synthesized event to the views listener')
		self.add_method('addEventListener','add an event listener for the instance to receive view triggered events')
		self.add_method('removeEventListener','remove a previously added event listener')
		self.add_method_property('fireEvent','name','string','name of the event')
		self.add_method_property('fireEvent','event','object','event object')
		self.add_method_property('addEventListener','name','string','name of the event')
		self.add_method_property('addEventListener','callback','function','callback function to invoke when the event is fired')
		self.add_method_property('removeEventListener','name','string','name of the event')
		self.add_method_property('removeEventListener','callback','function','callback function passed in addEventListener')
		
	def add_common_viewproxy_stuff(self):
		# these are common properties that all views inherit
		self.add_property('backgroundColor','string','the background color of the view')
		self.add_property('backgroundSelectedColor', 'string', 'the selected background color of the view. focusable must be true for normal views. (Android)')
		self.add_property('backgroundFocusedColor', 'string', 'the focused background color of the view. focusable must be true for normal views. (Android)')
		self.add_property('backgroundDisabledColor', 'string', 'the disabled background color of the view. (Android)')
		self.add_property('backgroundGradient','object','a background gradient for the view with the properties: type,startPoint,endPoint,startRadius,endRadius,backfillStart,backfillEnd,colors.')
		self.add_property('backgroundLeftCap','float','End caps specify the portion of an image that should not be resized when an image is stretched. This technique is used to implement buttons and other resizable image-based interface elements. When a button with end caps is resized, the resizing occurs only in the middle of the button, in the region between the end caps. The end caps themselves keep their original size and appearance. This property specifies the size of the left end cap. The middle (stretchable) portion is assumed to be 1 pixel wide. The right end cap is therefore computed by adding the size of the left end cap and the middle portion together and then subtracting that value from the width of the image')
		self.add_property('backgroundTopCap','float','End caps specify the portion of an image that should not be resized when an image is stretched. This technique is used to implement buttons and other resizable image-based interface elements. When a button with end caps is resized, the resizing occurs only in the middle of the button, in the region between the end caps. The end caps themselves keep their original size and appearance. This property specifies the size of the top end cap. The middle (stretchable) portion is assumed to be 1 pixel wide. The bottom end cap is therefore computed by adding the size of the top end cap and the middle portion together and then subtracting that value from the height of the image')
		self.add_property('animatedCenterPoint','object','read-only object with x and y properties of where the view is during animation')
		self.add_property('borderColor','string','the border color of the view')
		self.add_property('borderWidth','float','the border width of the view')
		self.add_property('borderRadius','float','the border radius of the view')
		self.add_property('backgroundImage','string','the background image url of the view')
		self.add_property('backgroundSelectedImage', 'string', 'the selected background image url of the view. focusable must be true for normal views. (Android)')
		self.add_property('backgroundFocusedImage', 'string', 'the focused background image url of the view. focusable must be true for normal views. (Android)')
		self.add_property('backgroundDisabledImage', 'string', 'the disabled background image url of the view. (Android)')
		self.add_property('zIndex','int','the z index position relative to other sibling views')
		self.add_property('opacity','float','the opacity from 0.0-1.0')
		self.add_property('anchorPoint','object','a dictionary with properties x and y to indicate the anchor point value. anchor specifies the position by which animation should occur. center is 0.5, 0.5')
		self.add_property('transform','object','the transformation matrix to apply to the view')
		self.add_property('center','object','a dictionary with properties x and y to indicate the center of the views position relative to the parent view')
		self.add_property('visible','boolean','a boolean of the visibility of the view')
		self.add_property('touchEnabled','boolean','a boolean indicating if the view should receive touch events (true, default) or forward them to peers (false)')
		self.add_property('size','object','the size of the view as a dictionary of width and height properties')
		self.add_property('width','float,string','property for the view width. Can be either a float value or a dimension string ie \'auto\' (default).')
		self.add_property('height','float,string','property for the view height. Can be either a float value or a dimension string ie \'auto\' (default).')
		self.add_property('top','float,string','property for the view top position. This position is relative to the view\'s parent. Can be either a float value or a dimension string ie \'auto\' (default).')
		self.add_property('left','float,string','property for the view left position. This position is relative to the view\'s parent. Can be either a float value or a dimension string ie \'auto\' (default).')
		self.add_property('right','float,string','property for the view right position. This position is relative to the view\'s parent. Can be either a float value or a dimension string ie \'auto\' (default).')
		self.add_property('bottom','float,string','property for the view bottom position. This position is relative to the view\'s parent. Can be either a float value or a dimension string ie \'auto\' (default).')
		self.add_property('softKeyboardOnFocus',['int', '-iphone','-ipad'],'One of Titanium.UI.Android.SOFT_KEYBOARD_DEFAULT_ON_FOCUS, Titanium.UI.Android.SOFT_KEYBOARD_HIDE_ON_FOCUS, or Titanium.UI.Android.SOFT_KEYBOARD_SHOW_ON_FOCUS. (Android only)')
		self.add_property('focusable',['boolean', '-iphone','-ipad'],'Set true if you want a view to be focusable when navigating with the trackball or D-Pad. Default: false. (Android Only)')
		# these are common methods
		self.add_method('add','add a child to the view hierarchy')
		self.add_method_property('add','view','object','the view to add to this views hiearchy')
		self.add_method('remove','remove a previously add view from the view hiearchy')
		self.add_method_property('remove','view','object','the view to remove from this views hiearchy')
		self.add_method('show','make the view visible')
		self.add_method('hide','hide the view')
		self.add_method('animate','animate the view')
		self.add_method_property('animate','obj','object','either a dictionary of animation properties or an Animation object')
		self.add_method_property('animate','callback','function','function to be invoked upon completion of the animation')
		self.add_method('toImage','return a Blob image of the rendered view','object')
		self.add_method_property('toImage','f','function','function to be invoked upon completion. if non-null, this method will be performed asynchronously. if null, it will be performed immediately')
		# these are common events
		self.add_event('swipe','fired when the device detects a swipe (left or right) against the view')
		self.add_event('singletap','fired when the device detects a single tap against the view')
		self.add_event('doubletap','fired when the device detects a double tap against the view')
		self.add_event('twofingertap','fired when the device detects a two-finger tap against the view')
		self.add_event('click','fired when the device detects a click (longer than touch) against the view')
		self.add_event('dblclick','fired when the device detects a double click against the view')
		self.add_event('touchstart','fired as soon as the device detects a gesture')
		self.add_event('touchmove','fired as soon as the device detects movement of a touch.  Event coordinates are always relative to the view in which the initial touch occurred')
		self.add_event('touchcancel','fired when a touch event is interrupted by the device. this happens in circumenstances such as an incoming call to allow the UI to clean up state.')
		self.add_event('touchend','fired when a touch event is completed')
		# font specials
		self.add_property('font-weight','string','the font weight, either normal or bold')
		self.add_property('font-size','string','the font size')
		self.add_property('font-style','string','the font style, either normal or italics')
		self.add_property('font-family','string','the font family')
		# common event properties
		self.add_event_property('swipe','direction','direction of the swipe - either left or right');
		for x in self.events:
			self.add_event_property(x['name'],'x','the x point of the event in receiving view coordiantes')
			self.add_event_property(x['name'],'y','the y point of the event, in receiving view coordinates')
			self.add_event_property(x['name'],'globalPoint','a dictionary with properties x and y describing the point of the event in screen coordinates')
	def set_type(self,typestr):
		self.typestr = typestr
	
	def set_subtype(self,typestr):
		self.subtype = typestr

	def set_returns(self,returns):
		self.returns = returns
	def set_notes(self,notes):
		self.notes = notes
	def add_method(self,key,value,returntype='void'):
		found = False
		for e in self.methods:
			if e['name'] == key:
				found = True
				e['value']=value
				e['returntype']=returntype
				e['since']=self.since
				break
		if found==False:
			self.methods.append({
				'name':key,
				'value':value,
				'parameters':[],
				'returntype':returntype,
				'since':self.since,
				'platforms':self.platforms,
				'filename':make_filename('method',self.namespace,key)})
		self.methods.sort(namesort)
	def set_method_returntype(self,key,value):
		tokens = value.split(';')
		the_type = tickerize(tokens[0])
		for m in self.methods:
			if m['name']==key:
				m['returntype'] = the_type
				m['deprecated'] = 'deprecated' in tokens
				m['platforms'] = resolve_supported_platforms(self.platforms, tokens)
				return
	def add_property(self,key,orig_specs,value):
		specs = orig_specs
		if isinstance(specs, basestring):
			specs = [ specs ]
		if len(specs) == 0:
			# We need at least type, which should be the first member of specs
			# Default to object
			specs = [ 'object' ]
		the_type = specs[0]

		# in case someone put a spec in with case
		specs = [x.lower() for x in orig_specs]
		# specs example: [int;classproperty;deprecated].  The type is always specs[0]
		if 'classproperty' in specs:
			classprop = True
		else:
			classprop = (key.upper() == key) # assume all upper case props are class constants
		deprecated = 'deprecated' in specs
		platforms = resolve_supported_platforms(self.platforms, specs)
		if len(platforms): # if not valid for any platform, don't add it.
			for prop in self.properties:
				if prop['name']==key:
					prop['type']=tickerize(the_type)
					prop['type_jsca'] = the_type
					prop['value']=value
					prop['isClassProperty']=classprop
					prop['deprecated'] = deprecated
					prop['platforms'] = resolve_supported_platforms(self.platforms, specs)
					prop['since'] = self.since
					return
			self.properties.append({
				'name':key,
				'type':tickerize(the_type),
				'type_jsca':the_type,
				'value':value,
				'isClassProperty':classprop,
				'deprecated':deprecated,
				'platforms':resolve_supported_platforms(self.platforms, specs),
				'since':self.since,
				'filename':make_filename('property',self.namespace,key)
				})
			self.properties.sort(namesort)
	def add_event(self,key,value):
		props = {}
		props['type'] = 'the name of the event fired'
		props['source'] = 'the source object that fired the event'
		found = False
		for e in self.events:
			if e['name']==key:
				e['value']=value
				found = True
				break
		if found==False:			
			self.events.append({'name':key,'value':value,'properties':props,'filename':make_filename('event',self.namespace,key)})
		self.events.sort(namesort)
	def add_event_property(self,event,key,value, orig_spec=None):
		for e in self.events:
			if e['name'] == event:
				e['properties'][key]=value
				return
	def add_method_property(self,name,fn,type,desc):
		for e in self.methods:
			if e['name'] == name:
				e['parameters'].append({'name':fn,'type':type,'description':desc})
	def add_platform(self,value):
		self.platforms.append(value)
	def add_example(self,desc,code):
		self.examples.append({'description':desc,'code':code})
	def add_parameter(self,name,typestr,desc):
		self.parameters.append({'name':name,'type':typestr,'description':desc})
		self.parameters.sort(namesort)
	def to_jsca(self):
		jsca_deprecated = False
		if self.deprecated:
			jsca_deprecated = True
		jsca_examples = []
		if self.examples:
			jsca_examples = [to_jsca_example(x) for x in self.examples]
		jsca_properties = []
		if self.properties:
			jsca_properties = [to_jsca_property(x) for x in self.properties if not x['name'].startswith('font-')]
		jsca_functions = []
		if self.methods:
			jsca_functions = [to_jsca_function(x) for x in self.methods]
		jsca_events = []
		if self.events:
			jsca_events = [to_jsca_event(x) for x in self.events]
		jsca_remarks = []
		if self.notes:
			jsca_remarks = [ self.notes ]
		result = {
				'name': clean_namespace(self.namespace),
				'description': self.description,
				'deprecated' : jsca_deprecated,
				'examples' : jsca_examples,
				'properties' : jsca_properties,
				'functions' : jsca_functions,
				'events' : jsca_events,
				'remarks' : jsca_remarks,
				'userAgents' : [ { 'platform' : x } for x in self.platforms ],
				'since' : [ { 'name': 'Titanium Mobile SDK', 'version' : self.since } ]
				}
		return to_ordered_dict(result, ('name',))
	def to_json(self):
		subs = []
		for s in self.objects:
			subs.append(s.namespace)
		result = {
			'methods' : self.methods,
			'properties' : self.properties,
			'events' : self.events,
			'examples' : self.examples,
			'platforms' : self.platforms,
			'description' : self.description,
			'type' : self.typestr,
			'subtype' : self.subtype,
			'returns' : self.returns,
			'since' : self.since,
			'deprecated' : self.deprecated,
			'parameters' : self.parameters,
			'notes' : self.notes,
			'objects' : subs
		}
		return result
	def get_filename(self):
		return make_filename(self.typestr, self.namespace)
	def get_parent_filename(self):
		if self.parent_namespace in apis:
			return apis[self.parent_namespace].get_filename()
	def finish_api_definition(self):
		if self.typestr == 'module' or self.subtype == 'view' or self.subtype == 'proxy':
			self.add_common_proxy_methods()
		if self.subtype == 'view':
			self.add_common_viewproxy_stuff()

def make_filename(objtype, namespace, name=None):
	fullname = name and '.'.join([namespace,name]) or namespace
	# "proxy" gets forcibly set to "object" at some point, so
	# so don't write out "-proxy" as the filename, else we'll
	# have broken links.
	if objtype == 'proxy':
		return '%s-object' % fullname
=======
ignore_dirs = (".git", ".svn", "CVS")
ignore_files = ("template.yml",)

def has_ancestor(one_type, ancestor_name):
	if one_type["name"] == ancestor_name:
		return True
	if "extends" in one_type and one_type["extends"] == ancestor_name:
		return True
	elif "extends" not in one_type:
		return False
>>>>>>> master
	else:
		parent_type_name = one_type["extends"]
		if (parent_type_name is None or not isinstance(parent_type_name, basestring) or
				parent_type_name.lower() == "object"):
			return False
		if not parent_type_name in apis:
			log.warn("%s extends %s but %s type information not found" % (one_type["name"],
				parent_type_name, parent_type_name))
			return False
		return has_ancestor(apis[parent_type_name], ancestor_name)

def is_titanium_module(one_type):
	return has_ancestor(one_type, "Titanium.Module")

def is_titanium_proxy(one_type):
	# When you use this, don't forget that modules are also proxies
	return has_ancestor(one_type, "Titanium.Proxy")

# iphone -> iPhone, etc.
def pretty_platform_name(name):
	if name.lower() == "iphone":
		return "iPhone"
	if name.lower() == "ipad":
		return "iPad"
	if name.lower() == "blackberry":
		return "Blackberry"
	if name.lower() == "android":
		return "Android"

def combine_platforms_and_since(annotated_obj):
	obj = annotated_obj.api_obj
	result = []
	platforms = None
	since = DEFAULT_SINCE
	if dict_has_non_empty_member(obj, "platforms"):
		platforms = obj["platforms"]
	# Method/property/event can't have more platforms than the types they belong to.
	if (platforms is None or
			isinstance(annotated_obj, AnnotatedMethod) or isinstance(annotated_obj, AnnotatedProperty) or
			isinstance(annotated_obj, AnnotatedEvent)):
		if annotated_obj.parent is not None:
			if dict_has_non_empty_member(annotated_obj.parent.api_obj, "platforms"):
				if platforms is None or len(annotated_obj.parent.api_obj["platforms"]) < len(platforms):
					platforms = annotated_obj.parent.api_obj["platforms"]
	# Last resort is the default list of platforms
	if platforms is None:
		platforms = DEFAULT_PLATFORMS
	if "since" in obj and len(obj["since"]) > 0:
		since = obj["since"]
	else:
		# If a method/event/property we can check type's "since"
		if (isinstance(annotated_obj, AnnotatedMethod) or isinstance(annotated_obj, AnnotatedProperty) or
				isinstance(annotated_obj, AnnotatedEvent)):
			if (annotated_obj.parent is not None and
					dict_has_non_empty_member(annotated_obj.parent.api_obj, "since")):
				since = annotated_obj.parent.api_obj["since"]

	since_is_dict = isinstance(since, dict)
	for name in platforms:
		one_platform = {"name": name, "pretty_name": pretty_platform_name(name)}
		if not since_is_dict:
			one_platform["since"] = since
		else:
			if name in since:
				one_platform["since"] = since[name]
			else:
				one_platform["since"] = DEFAULT_SINCE
		result.append(one_platform)

	return result

def load_one_yaml(filepath):
	f = None
	try:
		f = open(filepath, "r")
		types = [the_type for the_type in yaml.load_all(f)]
		return types
	except KeyboardInterrupt:
		raise
	except:
		e = traceback.format_exc()
		log.error("Exception occured while processing %s:" % filepath)
		for line in e.splitlines():
			log.error(line)
		return None
	finally:
		if f is not None:
			try:
				f.close()
			except:
				pass

def generate_output(options):
	for output_type in options.formats.split(","):
		try:
			__import__("generators.%s_generator" % output_type)
		except:
			log.error("Output format %s is not recognized" % output_type)
			sys.exit(1)
		if annotated_apis is None or len(annotated_apis) == 0:
			annotate_apis()
		generator = getattr(generators, "%s_generator" % output_type)
		generator.generate(apis, annotated_apis, options)

def process_yaml():
	global apis
	log.info("Parsing YAML files")
	for root, dirs, files in os.walk(this_dir):
		for name in ignore_dirs:
			if name in dirs:
				dirs.remove(name) # don't visit ignored directoriess
		for filename in files:
			if os.path.splitext(filename)[-1] != ".yml" or filename in ignore_files:
				continue
			filepath = os.path.join(root, filename)
			log.trace("Processing: %s" % filepath)
			types = None
			types = load_one_yaml(filepath)
			if types is None:
				log.trace("%s skipped" % filepath)
			else:
				for one_type in types:
					if one_type["name"] in apis:
						log.warn("%s has a duplicate" % one_type["name"])
					apis[one_type["name"]] = one_type

def annotate_apis():
	global apis, annotated_apis
	log.trace("Annotating api objects")
	for name in apis:
		log.trace("annotating %s" % name)
		one_api = apis[name]
		one_annotated_api = None
		if is_titanium_module(one_api):
			annotated_apis[name] = AnnotatedModule(one_api)
		elif is_titanium_proxy(one_api):
			annotated_apis[name] = AnnotatedProxy(one_api)
		else:
			if one_api["name"].startswith("Ti") and one_api["name"] != "Titanium.Event":
				# Titanium.Event is an exception because it doesn't extend anything and doesn't need
				# to be annotated as a Titanium type.
				log.warn("%s not being annotated as a Titanium type. Is its 'extends' property not set correctly?" % one_api["name"])
			else:
				# Types that are not true Titanium proxies and modules (like pseudo-types)
				# are treated as proxies for documentation generation purposes so that
				# their methods, properties, etc., can be documented.
				annotated_apis[name] = AnnotatedProxy(one_api)
	# Give each annotated api a direct link to its annotated parent
	for name in annotated_apis:
		if "." not in name:
			continue # e.g., "Titanium" has no parent
		else:
			parent_name = ".".join(name.split(".")[:-1])
			if parent_name not in annotated_apis:
				log.warn("%s's parent, %s, cannot be located" % (name, parent_name))
			else:
				annotated_apis[name].parent = annotated_apis[parent_name]

# Takes a documented api (module, proxy, method, property, event, etc.)
# originally from YAML and provides convenience properties and methods to
# assist with outputting to templates or other formats.
class AnnotatedApi(object):
	def __init__(self, api_obj):
		self.api_obj = api_obj
		self.name = api_obj["name"]
		self.parent = None
		self.typestr = "object"
		self.yaml_source_folder = ""
		self.inherited_from = ""
		if "deprecated" in api_obj:
			self.deprecated = api_obj["deprecated"]
		else:
			self.deprecated = None

	@lazyproperty
	def platforms(self):
		return combine_platforms_and_since(self)

class AnnotatedProxy(AnnotatedApi):
	def __init__(self, api_obj):
		AnnotatedApi.__init__(self, api_obj)
		self.typestr = "proxy"

	def build_method_list(self):
		methods = []
		if dict_has_non_empty_member(self.api_obj, "methods"):
			methods = [AnnotatedMethod(m, self) for m in self.api_obj["methods"]]
		self.append_inherited_methods(methods)
		return sorted(methods, key=lambda item: item.name)

	@lazyproperty
	def methods(self):
		return self.build_method_list();

	@lazyproperty
	def properties(self):
		properties = []
		if dict_has_non_empty_member(self.api_obj, "properties"):
			properties = [AnnotatedProperty(p, self) for p in self.api_obj["properties"]]
		self.append_inherited_properties(properties)
		return sorted(properties, key=lambda item: item.name)

	@lazyproperty
	def events(self):
		events = []
		if dict_has_non_empty_member(self.api_obj, "events"):
			events = [AnnotatedEvent(e, self) for e in self.api_obj["events"]]
		self.append_inherited_events(events)
		return sorted(events, key=lambda item: item.name)

	def append_inherited_attributes(self, att_list, att_list_name):
		if not "extends" in self.api_obj:
			return
		super_type_name = self.api_obj["extends"]
		class_type = {"properties": AnnotatedProperty, "methods": AnnotatedMethod,
				"events": AnnotatedEvent}[att_list_name]
		existing_names = [item.name for item in att_list]
		while (super_type_name is not None and len(super_type_name) > 0
				and super_type_name in apis):
			super_type = apis[super_type_name]
			if dict_has_non_empty_member(super_type, att_list_name):
				for new_item in super_type[att_list_name]:
					if new_item["name"] in existing_names:
						continue
					new_instance = class_type(new_item, self)
					new_instance.inherited_from = super_type_name
					att_list.append(new_instance)
					existing_names.append(new_item["name"])
			# Keep going up supertypes
			if "extends" in super_type:
				super_type_name = super_type["extends"]
			else:
				super_type_name = None

	def append_inherited_methods(self, methods):
		self.append_inherited_attributes(methods, "methods")

	def append_inherited_properties(self, properties):
		self.append_inherited_attributes(properties, "properties")

	def append_inherited_events(self, events):
		self.append_inherited_attributes(events, "events")

class AnnotatedModule(AnnotatedProxy):
	__create_proxy_template = None
	@classmethod
	def render_create_proxy_method(cls, method_template_obj):
		if cls.__create_proxy_template is None:
			template_text = open(os.path.join(this_dir, "templates", "create_proxy_method.yml.mako"), "r").read()
			cls.__create_proxy_template = Template(template_text)
		rendered = cls.__create_proxy_template.render(data=method_template_obj)
		return rendered

	def __init__(self, api_obj):
		AnnotatedProxy.__init__(self, api_obj)
		self.typestr = "module"
		self.yaml_source_folder = os.path.join(this_dir, self.name.replace(".", os.sep))

	def append_creation_methods(self, methods):
		proxies = self.member_proxies
		if proxies is None or len(proxies) == 0:
			return
		existing_names = [m.name for m in methods]
		for proxy in proxies:
			if proxy.name in not_real_titanium_types:
				continue
			if "createable" in proxy.api_obj and not proxy.api_obj["createable"]:
				continue
			method_name = "create%s" % proxy.name.split(".")[-1]
			if method_name in existing_names:
				continue
			method_template_obj = {"proxy_name": proxy.name}
			if "platforms" in proxy.api_obj:
				method_template_obj["platforms"] = yaml.dump(proxy.api_obj["platforms"])
			if "since" in proxy.api_obj:
				method_template_obj["since"] = yaml.dump(proxy.api_obj["since"])
			generated_method = yaml.load(AnnotatedModule.render_create_proxy_method(method_template_obj))
			methods.append(AnnotatedMethod(generated_method, self))

	@lazyproperty
	def member_proxies(self):
		global annotated_apis
		proxies = []
		for one_annotated_type in annotated_apis.values():
			if one_annotated_type.parent is self and one_annotated_type.typestr == "proxy":
				one_annotated_type.yaml_source_folder = self.yaml_source_folder
				proxies.append(one_annotated_type)
		return sorted(proxies, key=lambda item: item.name)

	@lazyproperty
	def methods(self):
		methods = self.build_method_list()
		self.append_creation_methods(methods)
		return sorted(methods, key=lambda item: item.name)

class AnnotatedMethod(AnnotatedApi):
	def __init__(self, api_obj, annotated_parent):
		AnnotatedApi.__init__(self, api_obj)
		self.typestr = "method"
		self.parent = annotated_parent
		self.yaml_source_folder = self.parent.yaml_source_folder

	@lazyproperty
	def parameters(self):
		parameters = []
		if dict_has_non_empty_member(self.api_obj, "parameters"):
			parameters = [AnnotatedMethodParameter(p, self) for p in self.api_obj["parameters"]]
		return parameters


class AnnotatedMethodParameter(AnnotatedApi):
	def __init__(self, api_obj, annotated_parent):
		AnnotatedApi.__init__(self, api_obj)
		self.parent = annotated_parent
		self.typestr = "parameter"
		self.yaml_source_folder = self.parent.yaml_source_folder

class AnnotatedProperty(AnnotatedApi):
	def __init__(self, api_obj, annotated_parent):
		AnnotatedApi.__init__(self, api_obj)
		self.typestr = "property"
		self.parent = annotated_parent
		self.yaml_source_folder = self.parent.yaml_source_folder

class AnnotatedEvent(AnnotatedApi):
	def __init__(self, api_obj, annotated_parent):
		AnnotatedApi.__init__(self, api_obj)
		self.typestr = "event"
		self.parent = annotated_parent
		self.yaml_source_folder = self.parent.yaml_source_folder

	@lazyproperty
	def properties(self):
		properties = []
		if dict_has_non_empty_member(self.api_obj, "properties"):
			properties = [AnnotatedProperty(p, self) for p in self.api_obj["properties"]]
		# Append properties from Titanium.Event.yml
		existing_names = [p.name for p in properties]
		event_super_type = apis.get("Titanium.Event")
		if event_super_type is not None and dict_has_non_empty_member(event_super_type, "properties"):
			for prop in event_super_type["properties"]:
				if prop["name"] in existing_names:
					continue
				new_prop = AnnotatedProperty(prop, self)
				new_prop.inherited_from = "Titanium.Event"
				properties.append(new_prop)
		return sorted(properties, key=lambda item: item.name)

<<<<<<< HEAD
def produce_vsdoc(config):
	if not config.has_key('output'):
		err("Required command line argument 'output' not provided")
		sys.exit(1)
			
	outdir = os.path.expanduser(config['output'])
	
	if not os.path.exists(outdir):
		os.makedirs(outdir)
	
	produce_vsdoc_output(config,outdir,apis)
	
def produce_vsdoc_output(config,outdir,theobj):
	lookupDir = TemplateLookup(directories=[os.path.join(template_dir,'templates')])
	
	filename = os.path.join(outdir,'Ti-vsdoc.js')
	f = open(filename,'w+')
	
	for name in sorted(theobj.iterkeys()):
		obj = theobj[name]
		# objects and modules have everything we need for the vsdoc
		if obj.typestr == 'module' or obj.typestr == 'object':
			output = lookupDir.get_template('module.vsdoc.html').render(config=config,data=obj)
			f.write(output)
	f.close()
	err('vsdoc created: ' + filename)
	
=======
>>>>>>> master
def main():
	global this_dir, log
	titanium_dir = os.path.dirname(this_dir)
	dist_apidoc_dir = os.path.join(titanium_dir, "dist", "apidoc")
	sys.path.append(os.path.join(titanium_dir, "build"))
	import titanium_version

	parser = optparse.OptionParser()
	parser.add_option("-f", "--formats",
			dest="formats",
			help='Comma-separated list of desired output formats.  "html" is default.',
			default="html")
	parser.add_option("--css",
			dest="css",
			help="Path to a custom CSS stylesheet to use in each HTML page",
			default=None)
	parser.add_option("-o", "--output",
			dest="output",
			help="Output directory for generated documentation",
			default=None)
	parser.add_option("-v", "--version",
			dest="version",
			help="Version of the API to generate documentation for",
			default=titanium_version.version)
	parser.add_option("--colorize",
			dest="colorize",
			action="store_true",
			help="Colorize code in examples",
			default=False)
	parser.add_option("--verbose",
			dest="verbose",
			action="store_true",
			help="Display verbose info messages",
			default=False)
	parser.add_option("--stdout",
			dest="stdout",
			action="store_true",
			help="Useful only for json/jsca. Writes the result to stdout. If you specify both --stdout and --output you'll get both an output file and the result will be written to stdout.",
			default=False)
	(options, args) = parser.parse_args()
	log_level = TiLogger.INFO
	if options.verbose:
		log_level = TiLogger.TRACE
	log = TiLogger(None, level=log_level, output_stream=sys.stderr)
	if options.output is None and "html" in options.formats:
		log.trace("Setting output folder to %s because html files will be generated and now --output folder was specified" % dist_apidoc_dir)
		options.output = dist_apidoc_dir
	process_yaml()
	generate_output(options)
	titanium_apis = [ta for ta in apis.values() if ta["name"].startswith("Ti")]
	log.info("%s Titanium types processed" % len(titanium_apis))

if __name__ == "__main__":
	main()
