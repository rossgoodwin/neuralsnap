
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

import os
import sys
import subprocess
import json
import re
from string import Template

class ImageNarrator(object):

    def __init__(self, output_title, ntalk_model_fp, rnn_model_fp, image_folder_fp,
                 stanza_len=512, num_steps=16, tgt_steps=[6,7,8,9],
                 highlight_color='#D64541', upload=False):
        self.upload = upload
        self.output_title = output_title
        self.ntalk_model_fp = ntalk_model_fp
        self.rnn_model_fp = rnn_model_fp
        self.image_folder_fp = image_folder_fp

        # Global Parameters

        # Adjust any of these (except num_images) to
        # alter your results

        self.num_images = '1'
        self.stanza_len = str(stanza_len)
        self.highlight_color = highlight_color # Valencia Red
        self.num_steps = num_steps
        self.tgt_steps = tgt_steps

        # Don't change these parameters unless
        # you have Karpath's repos cloned in
        # a different location

        self.SCRIPT_PATH = os.getcwd()
        self.NEURALTALK2_PATH = os.path.join(os.getcwd(), '..', 'neuraltalk2')
        self.CHARRNN_PATH = os.path.join(os.getcwd(), '..', 'char-rnn')

        self.expansion_obj_list = list()
        self.caption_list = list()
        self.html_fp = None
        self.url = None

    def get_result(self):
        self.narrate()
        self.process_to_html()
        if self.upload:
            return self.url
        else:
            return 'file://'+self.html_fp

    def narrate(self):
        # NeuralTalk2 Image Captioning

        os.chdir(self.NEURALTALK2_PATH)

        ntalk_cmd_list = [
            'th',
            'eval.lua',
            '-model',
            self.ntalk_model_fp,
            '-image_folder',
            self.image_folder_fp,
            '-num_images',
            self.num_images,
            '-gpuid',
            '-1'
        ]

        print "INIT NEURALTALK2 CAPTIONING"

        ntalk_proc = subprocess.Popen(ntalk_cmd_list)
        ntalk_proc.communicate()


        # Load Captions


        with open(self.NEURALTALK2_PATH+'/vis/vis.json') as caption_json:
            caption_obj_list = json.load(caption_json)
            
        caption_obj_list *= self.num_steps


        # RNN Caption Expansion


        os.chdir(self.CHARRNN_PATH)

        print "INIT CHAR-RNN EXPANSION"

        for i in self.tgt_steps:
            obj = caption_obj_list[i]
            caption = obj['caption']
            prepped_caption = caption[0].upper() + caption[1:]
            
            temp = str((i+1.0)/float(self.num_steps))
            print "EXPANDING AT TEMPERATURE " + temp
            
            rnn_cmd_list = [
                'th',
                'sample.lua',
                self.rnn_model_fp,
                '-length',
                self.stanza_len,
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
            
            self.expansion_obj_list.append({
                'id': obj['image_id'],
                'text': expansion
            })
            
            self.caption_list.append((prepped_caption, '<span style="color:'+self.highlight_color+';">'+prepped_caption+'</span>'))

        # Back to original working directory
        os.chdir(self.SCRIPT_PATH)


    # Post Processing

    def process_to_html(self):
        img_fps = map(
            lambda x: os.path.join(self.NEURALTALK2_PATH, 'vis', 'imgs', 'img%s.jpg'%x['id']),
            self.expansion_obj_list
        )

        if self.upload:
            from upload_to_s3 import upload
            img_url = upload(img_fps.pop())
        else:
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
            self.expansion_obj_list
        )

        exps_tups = zip(expansions, self.caption_list)


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


        with open(self.SCRIPT_PATH+'/template.html', 'r') as tempfile:
            html_temp_str = tempfile.read()
            
        html_temp = Template(html_temp_str)
        html_result = html_temp.substitute(title=self.output_title, body=body_html)
        html_fp = '%s/pages/%s.html' % (self.SCRIPT_PATH, re.sub(r'\W+', '_', self.output_title))


        # Save HTML File

        with open(html_fp, 'w') as outfile:
            outfile.write(html_result)

        self.html_fp = html_fp

        if self.upload:
            self.url = upload(html_fp)
    

if __name__ == '__main__':
    # Start Clock
    import time
    start_time = time.time()

    # Instatiate expander object
    script, output_title, ntalk_model_fp, rnn_model_fp, image_folder_fp = sys.argv
    expander = ImageNarrator(output_title, ntalk_model_fp, rnn_model_fp, image_folder_fp)

    # Narrate, process, and open HTML File
    import webbrowser
    webbrowser.open_new_tab(expander.get_result())

    # Print Runtime
    end_time = time.time()
    print end_time - start_time

