# "All the time the sun / Is wheeling out of a dark bright ground."

A new year, a new word camera: uses artificial neural networks to generate poetry from images.

This project, in many ways a follow-up on [word.camera](https://word.camera), was created on the shoulders of two spectacular open source contributions by [Andrej Karpathy](https://github.com/karpathy): [NeuralTalk2](https://github.com/karpathy/neuraltalk) and [Char-RNN](https://github.com/karpathy/char-rnn), both of which run in [Torch](http://torch.ch/). The code I've provided in this repository is a modest Python wrapper for a few of Karpathy's scripts, and a means to experiment with a few models that I've trained on [Nvidia K80 GPUs](http://www.nvidia.com/object/tesla-k80.html) using the High Performance Computing facilities at NYU.

In my research, I am developing tools that I hope will serve to augment human creativity. These are the first neural network models to emerge from my explorations, and I've decided to make them available to others:

    $ wget https://s3.amazonaws.com/rossgoodwin/models/2016-01-12_char-rnn_model_01_rg.t7
    $ wget https://s3.amazonaws.com/rossgoodwin/models/2016-01-12_char-rnn_model_02_rg.t7
    $ wget https://s3.amazonaws.com/rossgoodwin/models/2016-01-12_neuraltalk2_model_01_rg.t7

## How It Works

[NeuralTalk2](https://github.com/karpathy/neuraltalk) uses [convolutional](https://en.wikipedia.org/wiki/Convolutional_neural_network) and [recurrent](https://en.wikipedia.org/wiki/Recurrent_neural_network) neural networks to caption images. I trained my own model on the [MSCOCO dataset](http://mscoco.org/), using the general guidelines Karpathy outlines in his documentation, but made adjustments to increase verbosity.

I then trained recurrent neural networks using [Char-RNN](https://github.com/karpathy/char-rnn) on about 40MB of (mostly) 20th-century poetry from a variety of writers (and a variety of cultures) around the world.

In the output examples below, the red text is the image caption, and the poetry-trained net generated the rest of the text. The stanzas iterate through different RNN "temperature" values, an input that controls the riskiness of the model's predictions. Lower temperature results will be more repetitive and strictly grammatical, while higher temperature results contain more variety but may also contain more errors.

## How To Run It

I have tested this software on Ubuntu 14.04 and 15.10. You can try other OS options at your own risk -- in theory, it should run on anything that can run Torch and Python, although I've heard that [NeuralTalk2 does not play nice with the Raspberry Pi](https://github.com/SaMnCo/docker-neuraltalk2).

You'll need to clone the [NeuralTalk2](https://github.com/karpathy/neuraltalk) and [Char-RNN](https://github.com/karpathy/char-rnn) repos into the main folder, then follow Karpathy's README instructions to install the dependencies for NeuralTalk2 -- you don't need to worry about any of the GPU or training stuff, unless you want to use your own models. (The models I've provided are calibrated to run on CPUs.) Thankfully, the dependencies of Char-RNN are a subset of those required for NeuralTalk2.

## Usage

    $ python neuralsnap.py <output_title> <ntalk_model_filepath> <rnn_model_filepath> <image_folder_filepath>

e.g.

    $ python neuralsnap.py testing123 /path/to/neuraltalk2/model/2016-01-12_neuraltalk2_model_01_rg.t7 /path/to/char-rnn/model/2016-01-12_char-rnn_model_02_rg.t7 /path/to/image/folder

## Sample Output

* [Rothko painting](https://s3.amazonaws.com/rossgoodwin/neuralsnap/145215747186_Epoch_59_24_Loss_1_1455_Dropout_0_25_512_16_2_4_6_8_Rothko.html)
* [Ikeda installation](https://s3.amazonaws.com/rossgoodwin/neuralsnap/145237613476_Epoch_64_24_Loss_1_1434_Dropout_0_25_512_16_8_9_7_Ikeda.html)
* [Airplanes](https://s3.amazonaws.com/rossgoodwin/neuralsnap/145240870834_Epoch_64_24_Loss_1_1434_Dropout_0_25_512_16_6_7_8_9_Planes.html)
* [Keys](https://s3.amazonaws.com/rossgoodwin/neuralsnap/145240853879_Epoch_64_24_Loss_1_1434_Dropout_0_25_512_16_6_7_8_9_Keys.html)
* [Mies Van Der Rohe](https://s3.amazonaws.com/rossgoodwin/neuralsnap/145232647105_Epoch_83_51_Loss_1_1439_Dropout_0_25_512_16_3_5_7_Mies_Van_Der_Rohe.html)