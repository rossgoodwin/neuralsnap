
# coding: utf-8

# NeuralSnap image-to-text poetry generator
# Copyright (C) 2016  Ross Goodwin

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

# You may contact Ross Goodwin via email at ross.goodwin@gmail.com or
# address physical correspondence to:

#                     Ross Goodwin c/o ITP
#                     721 Broadway, 4th Floor
#                     New York, NY 10003


# NeuralSnap
# 
# Works by generating a caption for an image with recurrent and
# convolutional neural networks using NeuralTalk2. That
# (brief) caption is then expanded into a poem using a second
# recurrent neural network.
# 
# Ross Goodwin, 2016

import time
start_time = time.time()

import os
import sys
import subprocess
import json
import re
from string import Template

script, output_title, ntalk_model_fp, rnn_model_fp, image_folder_fp = sys.argv

# Global Parameters

# Adjust any of these (except num_images) to
# alter your results

num_images = '1'
stanza_len = '512'
highlight_color = '#D64541' # Valencia Red
num_steps = 16
tgt_steps = [6,7,8,9]

# Don't change these parameters

SCRIPT_PATH = os.getcwd()
NEURALTALK2_PATH = os.path.join(os.getcwd(), '..', 'neuraltalk2')
CHARRNN_PATH = os.path.join(os.getcwd(), '..', 'char-rnn')


# NeuralTalk2 Image Captioning


os.chdir(NEURALTALK2_PATH)

ntalk_cmd_list = [
    'th',
    'eval.lua',
    '-model',
    ntalk_model_fp,
    '-image_folder',
    image_folder_fp,
    '-num_images',
    num_images,
    '-gpuid',
    '-1'
]

print "INIT NEURALTALK2 CAPTIONING"

ntalk_proc = subprocess.Popen(ntalk_cmd_list)
ntalk_proc.communicate()


# Load Captions


with open(NEURALTALK2_PATH+'/vis/vis.json') as caption_json:
    caption_obj_list = json.load(caption_json)
    
caption_obj_list *= num_steps


# RNN Caption Expansion


os.chdir(CHARRNN_PATH)

expansion_obj_list = list()
caption_list = list()

print "INIT CHAR-RNN EXPANSION"

for i in tgt_steps:
    obj = caption_obj_list[i]
    caption = obj['caption']
    prepped_caption = caption[0].upper() + caption[1:]
    
    temp = str((i+1.0)/float(num_steps))
    print "EXPANDING AT TEMPERATURE " + temp
    
    rnn_cmd_list = [
        'th',
        'sample.lua',
        rnn_model_fp,
        '-length',
        stanza_len,
        '-verbose',
        '0',
        '-temperature',
        temp,
        '-primetext',
        prepped_caption,
        '-gpuid',
        '-1'
    ]

    rnn_proc = subprocess.Popen(
        rnn_cmd_list,
        stdout=subprocess.PIPE
    )
    expansion = rnn_proc.stdout.read()
    
    expansion_obj_list.append({
        'id': obj['image_id'],
        'text': expansion
    })
    
    caption_list.append((prepped_caption, '<span style="color:'+highlight_color+';">'+prepped_caption+'</span>'))


# Post Processing


img_fps = map(
    lambda x: os.path.join(NEURALTALK2_PATH, 'vis', 'imgs', 'img%s.jpg'%x['id']),
    expansion_obj_list
)

img_url = img_fps.pop()


def fix_end_punctuation(exp):
    try:
        first_sentence, remainder = exp.rsplit('.', 1)
        first_sentence = first_sentence.strip()
        if remainder[0] in ["\'", '\"', '”', '’']:
            first_sentence += '.' + remainder[0]
        else:
            first_sentence += '.'
        return first_sentence
    except:
        return exp.rsplit(' ', 1)[0] + '...'

expansions = map(
    lambda x: fix_end_punctuation(x['text']),
    expansion_obj_list
)

exps_tups = zip(expansions, caption_list)


def add_span(exp, tup):
    original, modified = map(lambda x: x.decode('utf8').encode('ascii', 'xmlcharrefreplace'), tup)
    return exp.replace(original, modified)
    
final_exps = map(lambda (x,y): add_span(x,y), exps_tups)


def make_html_block(exp):
    exp_ascii = exp.decode('utf8').encode('ascii', 'xmlcharrefreplace')
    exp_ascii = exp_ascii.replace('\n', '</p><p>')
    return '<p>%s</p>' % exp_ascii

img_block = '<p class="text-center"><a href="%s"><img src="%s" width="275px" class="img-thumbnail"></a></p>' % (img_url, img_url)
body_html = img_block + '\n'.join(map(make_html_block, final_exps))


with open(SCRIPT_PATH+'/template.html', 'r') as tempfile:
    html_temp_str = tempfile.read()
    
html_temp = Template(html_temp_str)
html_result = html_temp.substitute(title=output_title, body=body_html)
html_fp = '%s/pages/%s.html' % (SCRIPT_PATH, re.sub(r'\W+', '_', output_title))


# Save HTML File

with open(html_fp, 'w') as outfile:
    outfile.write(html_result)
    

# Print Runtime

end_time = time.time()
print end_time - start_time


# Open HTML File

import webbrowser

webbrowser.open_new_tab('file://'+html_fp)

