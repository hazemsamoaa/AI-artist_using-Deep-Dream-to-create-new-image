# -*- coding: utf-8 -*-
"""AI artist_using Deep Dream to create new image.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1OORL1hw3dv7atuw7WzpjVAspWuvAhWHD
"""

!pip install tensorflow-gpu==2.0.0.alpha0

import tensorflow as tf

tf.__version__

import pandas as pd # used for data frame manipulation
import numpy as np # numerical analysis 
import matplotlib.pyplot as plt # data visulaization and data plotting 
import seaborn as sns # data visulaization and data plotting 
import random

# let's used the base trained model of Inception (google network)
# we will not include the head of the network 
# we will specify the weight to be equal to imagenet
base_model = tf.keras.applications.InceptionV3(include_top = False,weights = 'imagenet')
# imagenet is a repository of millions of images and tons of classes

################# Optional to run ###########################
base_model.summary()
# we will see mixed0 (Concatenate) which is concatenation of multiple activations or multiple kind of outputs. 
# there are many mixed [0->10]
# now in Deep dream we want to specify which kayer or activation I'm interested in.

# choose the mixed layer and maximize the activation of those layers or in other words maximize the loss which is the activations generated by the layer of interest.
# Randomly we will start to pick up layers 
names  = ['mixed3','mixed5']
#names = ['mixed3', 'mixed5', 'mixed8', 'mixed9']
# we will loop thought the names in the base_model 
layers = [base_model.get_layer(name).output for name in names] # here we pickup only preffered layers from the model 
# now we will define our deep dream model 
# to do that we will specify the inputs and then outputs (the layers that I'm intertested in) [we are intertested in the activation coming from mixed3 and mixed5]
deepdream_model = tf.keras.Model(inputs = base_model.input,outputs = layers)

from google.colab import drive
drive.mount('/content/drive')

################ Optional to run ############################
# load image
sample_image = tf.keras.preprocessing.image.load_img(r'/content/drive/My Drive/Colab Notebooks/StaryNight (1).jpg',target_size=(225,375))
plt.imshow(sample_image)
print("Original Image Shape is: {}".format(np.shape(sample_image)))
# the shape that I've selected when I load the image.

# Normalize the image to have pixels between 0-1 to do that 
# we convert the pixel matrix into array 
# then divide by 255.0
sample_image = np.array(sample_image)/255.0
print ("The minimum Pixel value: {}".format(sample_image.min()))
print ("The maximum Pixel value: {}".format(sample_image.max()))

################ Optional to run ############################
# Now we will feed in the image into our pretrained model
# firstly tp preprocess the image we need to convert it to array 
sample_image = tf.keras.preprocessing.image.img_to_array(sample_image)
print ("the array image shape is: ",sample_image.shape)

################ Optional to run ############################
# preprocess the image on the basis of the model. which means addapt image to the input that accepted by the model
sample_image = tf.keras.applications.inception_v3.preprocess_input(sample_image)
# expand the image to be as a batch format 
sample_image = tf.expand_dims(sample_image,axis=0)
print ("The new image shape after patch adding is : ",sample_image.shape)

################ Optional to run ############################
# run our activation 
activation = deepdream_model(sample_image)
activation
# those are the outputs comming out from my activation

################ Optional to run ############################
print ("Activation shape is: ",np.shape(activation))
# here we have 2 activations, and each one of them is sized to be 1*12*21*768 (that the expected out from mix3 and mix5)

# calculate the loss of the deep dream 
# the objective here is to select a layer -> maximize the loss [which is the activation generated from this layer]
# we will calculate the loss which is the sum of activations for a given layer
# to maximize the loss we have to use gradient ascent 
# ----> the function feedforward the image through the network and generate activations 
# ----> obtain the average and sum of those outputs 
def loss_calculation (image,model):
  batched_image = tf.expand_dims(image,axis=0)
  activation_layers = model(batched_image) #just run the model
  print ('The Value of Activation (Output Layer)= ', activation_layers)
  print ('The Sahpe of Activation = ', np.shape(activation_layers))
  losses = []
  for act in activation_layers:
    loss = tf.math.reduce_mean(act) # calculate the mean of each activation (loss per layer)
    losses.append(loss)
  print ('losses for the activation layer are:',losses)
  print ('losses shape = ', np.shape(losses))
  print ('Sum of losses', tf.reduce_sum(losses)) # we have multiple losses comming out from multiple layers all what I need is to come up with 
  # one single number, so we want to maxizmize this number at the end.

  return tf.reduce_sum(losses)

################ Optional to run ############################

# Now we will test our build in function 
Sample_Image= tf.keras.preprocessing.image.load_img(r'/content/drive/My Drive/Colab Notebooks/StaryNight (1).jpg', target_size = (225, 375))
Sample_Image = np.array(Sample_Image)/255.0
Sample_Image = tf.keras.preprocessing.image.img_to_array(Sample_Image)
Sample_Image = tf.Variable(tf.keras.applications.inception_v3.preprocess_input(Sample_Image))

loss_calculation(Sample_Image,deepdream_model)

"""we will take the computed loss and we will calc the gradient of that loss w.r.t pixels of the input image [d(activations\loss/d(input image))]
take that gradient (multiplied by learning rate) and added it to the input added image
I will obtain a new image with enhanced feature, then I will repeat and iterate the process again and again 
new image = old_image + greditent * learning _rate
When we annotate a function with tf.function, the function can be called like any other python defined function but the \n
benefit is that it will be compiled into a graph so it will be much faster and could be executed over TPU/GPU
"""

@tf.function
def deepdream(model, image, step_size):
    with tf.GradientTape() as tape:
      # to obtain the gradient and recod all the progress that happened through out the training 
      # This needs gradients relative to `img`
      # `GradientTape` only watches `tf.Variable`s by default
      tape.watch(image)
      loss = loss_calculation(image, model) # call the function that calculate the loss 

    # Calculate the gradient of the loss with respect to the pixels of the input image.
    # The syntax is as follows: dy_dx = g.gradient(y, x) 
    gradients = tape.gradient(loss, image)

    print('GRADIENTS =\n', gradients)
    print('GRADIENTS SHAPE =\n', np.shape(gradients))

    # tf.math.reduce_std computes the standard deviation of elements across dimensions of a tensor
     # to normalize my gradient we will divide by standard deviation of gradient 
    gradients /= tf.math.reduce_std(gradients)  

    # In gradient ascent, the "loss" is maximized so that the input image increasingly "excites" the layers.
    # You can update the image by directly adding the gradients (because they're the same shape!)
    # now we are ready to update out image
    image = image + gradients * step_size
    # now we will clip the new image to make it from -1 to +1
    image = tf.clip_by_value(image, -1, 1)

    return loss, image

"""define the run function for the model. It's like the compile"""

def run_deep_dream_simple(model, image, steps=100, step_size=0.01):
  # those are the default values if I didn't recieve any paratmeter when I call the function
  # Convert from uint8 to the range expected by the model.
  image = tf.keras.applications.inception_v3.preprocess_input(image)

  for step in range(steps):
    # we will go a head many times, every time we will call our deep dream model 
    loss, image = deepdream(model, image, step_size)
    # here we want to check and show the progress every 100 steps 
    if step % 100 == 0:
      plt.figure(figsize=(12,12))
      plt.imshow(deprocess(image))
      plt.show()
      print ("Step {}, loss {}".format(step, loss))

  # clear_output(wait=True)
  plt.figure(figsize=(12,12))
  # we will see the final value of the image 
  # here we will visualize the image after normaliazation that's why we will invoke the function that we defined down 
  plt.imshow(deprocess(image))
  plt.show()
  # return the final image 
  return deprocess(image)

def deprocess (image):
  image = 255*(image +1.0) /2.0
  return tf.cast(image,tf.uint8)

# final run 
# read the image -> convert it into array -> then invoke the run model
Sample_Image= tf.keras.preprocessing.image.load_img(r'/content/drive/My Drive/Colab Notebooks/StaryNight (1).jpg', target_size = (225, 375))
Sample_Image = np.array(Sample_Image)
dearm_img = run_deep_dream_simple(deepdream_model,Sample_Image,2000,0.001)

# to enhance the performance of the model we could run the model on a various size of image
# so image become a lot more smoother 
# we will define an OCTAVE_SCALE, -> run the algorithm but on differnt sizes
# The idea here is to obtain the changes that we want in few steps => the performance become much much better.

OCTAVE_SCALE = 1.3
# reading (loading) the image
image = tf.keras.preprocessing.image.load_img(r'/content/drive/My Drive/Colab Notebooks/StaryNight (1).jpg',target_size=(225,375))
# convert it into array
image = tf.constant(np.array(image))
# get the original shape of the image without the channels 
base_shape = tf.cast(tf.shape(image)[:-1],tf.float32)

# now iterate for many times and resize the image accordingly 
# we will repeat the algorithms 5 times each for one specific shape.
for n in range (5):
  # define new shape and reflect it to the image
  # at each time we add OCTAVE SCALE to the power of n then multiply with 2D array of base shape of image.

  new_shape = tf.cast(base_shape*(OCTAVE_SCALE**n),tf.int32)
  image = tf.image.resize(image,new_shape).numpy()
  image = run_deep_dream_simple(model=deepdream_model,image=image,steps=400,step_size=0.001)

show(image)

"""Incridble results having a smooth image just by using few steps just by resizing the image."""

