# -*- coding: utf-8 -*-
"""CIFAR10GAN2.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1knTQ1pWSbmcJDsvAXta-yUVDkGt4BINX

Code from:
https://machinelearningmastery.com/how-to-develop-a-generative-adversarial-network-for-a-cifar-10-small-object-photographs-from-scratch/
How to Develop a GAN to Generate CIFAR10 Small Color Photographs
by Jason Brownlee on July 1, 2019 in Generative Adversarial Networks

and from
https://machinelearningmastery.com/how-to-develop-a-cnn-from-scratch-for-cifar-10-photo-classification/

How to Develop a CNN From Scratch for CIFAR-10 Photo Classification
by Jason Brownlee on May 13, 2019 in Deep Learning for Computer Vision
"""

from numpy import expand_dims
from numpy import zeros
from numpy import ones
from numpy import vstack
from numpy.random import randn
from numpy.random import randint
from keras.datasets.cifar10 import load_data
from keras.optimizers import Adam
from keras.models import Sequential
from keras.layers import Dense
from keras.layers import Reshape
from keras.layers import Flatten
from keras.layers import Conv2D
from keras.layers import Conv2DTranspose
from keras.layers import LeakyReLU
from keras.layers import Dropout
from keras.models import load_model  # Add this line
from matplotlib import pyplot

# Load pre-trained models
classification_model = load_model('/content/final_model.h5')
gan_model = load_model('/content/generator_model_200.h5')

# define the standalone discriminator model
def define_discriminator(in_shape=(32,32,3)):
	model = Sequential()
	# normal
	model.add(Conv2D(64, (3,3), padding='same', input_shape=in_shape))
	model.add(LeakyReLU(alpha=0.2))
	# downsample
	model.add(Conv2D(128, (3,3), strides=(2,2), padding='same'))
	model.add(LeakyReLU(alpha=0.2))
	# downsample
	model.add(Conv2D(128, (3,3), strides=(2,2), padding='same'))
	model.add(LeakyReLU(alpha=0.2))
	# downsample
	model.add(Conv2D(256, (3,3), strides=(2,2), padding='same'))
	model.add(LeakyReLU(alpha=0.2))
	# classifier
	model.add(Flatten())
	model.add(Dropout(0.4))
	model.add(Dense(1, activation='sigmoid'))
	# compile model
	opt = Adam(lr=0.0002, beta_1=0.5)
	model.compile(loss='binary_crossentropy', optimizer=opt, metrics=['accuracy'])
	return model

# define the standalone generator model
def define_generator(latent_dim):
	model = Sequential()
	# foundation for 4x4 image
	n_nodes = 256 * 4 * 4
	model.add(Dense(n_nodes, input_dim=latent_dim))
	model.add(LeakyReLU(alpha=0.2))
	model.add(Reshape((4, 4, 256)))
	# upsample to 8x8
	model.add(Conv2DTranspose(128, (4,4), strides=(2,2), padding='same'))
	model.add(LeakyReLU(alpha=0.2))
	# upsample to 16x16
	model.add(Conv2DTranspose(128, (4,4), strides=(2,2), padding='same'))
	model.add(LeakyReLU(alpha=0.2))
	# upsample to 32x32
	model.add(Conv2DTranspose(128, (4,4), strides=(2,2), padding='same'))
	model.add(LeakyReLU(alpha=0.2))
	# output layer
	model.add(Conv2D(3, (3,3), activation='tanh', padding='same'))
	return model

# define the combined generator and discriminator model, for updating the generator
def define_gan(g_model, d_model):
	# make weights in the discriminator not trainable
	d_model.trainable = False
	# connect them
	model = Sequential()
	# add generator
	model.add(g_model)
	# add the discriminator
	model.add(d_model)
	# compile model
	opt = Adam(lr=0.0002, beta_1=0.5)
	model.compile(loss='binary_crossentropy', optimizer=opt)
	return model

# load and prepare cifar10 training images
def load_real_samples():
	# load cifar10 dataset
	(trainX, _), (_, _) = load_data()
	# convert from unsigned ints to floats
	X = trainX.astype('float32')
	# scale from [0,255] to [-1,1]
	X = (X - 127.5) / 127.5
	return X

# select real samples
def generate_real_samples(dataset, n_samples):
	# choose random instances
	ix = randint(0, dataset.shape[0], n_samples)
	# retrieve selected images
	X = dataset[ix]
	# generate 'real' class labels (1)
	y = ones((n_samples, 1))
	return X, y

# generate points in latent space as input for the generator
def generate_latent_points(latent_dim, n_samples):
	# generate points in the latent space
	x_input = randn(latent_dim * n_samples)
	# reshape into a batch of inputs for the network
	x_input = x_input.reshape(n_samples, latent_dim)
	return x_input

# use the generator to generate n fake examples, with class labels
def generate_fake_samples(g_model, latent_dim, n_samples):
	# generate points in latent space
	x_input = generate_latent_points(latent_dim, n_samples)
	# predict outputs
	X = g_model.predict(x_input)
	# create 'fake' class labels (0)
	y = zeros((n_samples, 1))
	return X, y

# create and save a plot of generated images
def save_plot(examples, epoch, n=7):
	# scale from [-1,1] to [0,1]
	examples = (examples + 1) / 2.0
	# plot images
	for i in range(n * n):
		# define subplot
		pyplot.subplot(n, n, 1 + i)
		# turn off axis
		pyplot.axis('off')
		# plot raw pixel data
		pyplot.imshow(examples[i])
	# save plot to file
	filename = 'generated_plot_e%03d.png' % (epoch+1)
	pyplot.savefig(filename)
	pyplot.close()

# evaluate the discriminator, plot generated images, save generator model
def summarize_performance(epoch, g_model, d_model, dataset, latent_dim, n_samples=150):
	# prepare real samples
	X_real, y_real = generate_real_samples(dataset, n_samples)
	# evaluate discriminator on real examples
	_, acc_real = d_model.evaluate(X_real, y_real, verbose=0)
	# prepare fake examples
	x_fake, y_fake = generate_fake_samples(g_model, latent_dim, n_samples)
	# evaluate discriminator on fake examples
	_, acc_fake = d_model.evaluate(x_fake, y_fake, verbose=0)
	# summarize discriminator performance
	print('>Accuracy real: %.0f%%, fake: %.0f%%' % (acc_real*100, acc_fake*100))
	# save plot
	save_plot(x_fake, epoch)
	# save the generator model tile file
	filename = 'generator_model_%03d.h5' % (epoch+1)
	g_model.save(filename)

# train the generator and discriminator
def train(g_model, d_model, gan_model, dataset, latent_dim, n_epochs=200, n_batch=128):
	bat_per_epo = int(dataset.shape[0] / n_batch)
	half_batch = int(n_batch / 2)
	# manually enumerate epochs
	for i in range(n_epochs):
		# enumerate batches over the training set
		for j in range(bat_per_epo):
			# get randomly selected 'real' samples
			X_real, y_real = generate_real_samples(dataset, half_batch)
			# update discriminator model weights
			d_loss1, _ = d_model.train_on_batch(X_real, y_real)
			# generate 'fake' examples
			X_fake, y_fake = generate_fake_samples(g_model, latent_dim, half_batch)
			# update discriminator model weights
			d_loss2, _ = d_model.train_on_batch(X_fake, y_fake)
			# prepare points in latent space as input for the generator
			X_gan = generate_latent_points(latent_dim, n_batch)
			# create inverted labels for the fake samples
			y_gan = ones((n_batch, 1))
			# update the generator via the discriminator's error
			g_loss = gan_model.train_on_batch(X_gan, y_gan)
			# summarize loss on this batch
			if (j+1) % 50 == 0:
				print('>%d, %d/%d, d1=%.3f, d2=%.3f g=%.3f' %
					(i+1, j+1, bat_per_epo, d_loss1, d_loss2, g_loss))
		# evaluate the model performance, sometimes
		if (i+1) % 10 == 0:
			summarize_performance(i, g_model, d_model, dataset, latent_dim)

# Main entry point
if __name__ == "__main__":
    # load and prepare cifar10 training images
    dataset = load_real_samples()

    # define the size of the latent space
    latent_dim = 100

    # create the discriminator
    d_model = define_discriminator()

    # create the generator
    g_model = define_generator(latent_dim)

    # create the gan
    gan_model = define_gan(g_model, d_model)

    # train model
    train(g_model, d_model, gan_model, dataset, latent_dim, n_epochs=50)

# Generation of 100 fake pictures
# example of loading the generator model and generating images
from keras.models import load_model
from numpy.random import randn
from matplotlib import pyplot

# generate points in latent space as input for the generator
def generate_latent_points(latent_dim, n_samples):
	# generate points in the latent space
	x_input = randn(latent_dim * n_samples)
	# reshape into a batch of inputs for the network
	x_input = x_input.reshape(n_samples, latent_dim)
	return x_input

# plot the generated images
def create_plot(examples, n):
	# plot images
	for i in range(n * n):
		# define subplot
		pyplot.subplot(n, n, 1 + i)
		# turn off axis
		pyplot.axis('off')
		# plot raw pixel data
		pyplot.imshow(examples[i, :, :])
	pyplot.show()

# load model
model = load_model('generator_model_200.h5')
#model = load_model('generator_model_050.h5')
# generate images
latent_points = generate_latent_points(100, 100)
# generate images
X = model.predict(latent_points)
# scale from [-1,1] to [0,1]
X = (X + 1) / 2.0
# plot the result
create_plot(X, 10)
print(generate_latent_points(1, 1))

#Example of plotting the first image of the first three rows, one by one
#plot the result
pyplot.imshow(X[0, :, :])
pyplot.show()
pyplot.imshow(X[10, :, :])
pyplot.show()
pyplot.imshow(X[20, :, :])
pyplot.show()

# We fit a CIFAR10 CNN classification model and save the final model to a file
from keras.datasets import cifar10
from keras.utils import to_categorical
from keras.models import Sequential
from keras.layers import Conv2D
from keras.layers import MaxPooling2D
from keras.layers import Dense
from keras.layers import Flatten
from keras.optimizers import SGD

# load train and test dataset
def load_dataset():
 # load dataset
 (trainX, trainY), (testX, testY) = cifar10.load_data()
 # one hot encode target values
 trainY = to_categorical(trainY)
 testY = to_categorical(testY)
 return trainX, trainY, testX, testY

# scale pixels
def prep_pixels(train, test):
 # convert from integers to floats
 train_norm = train.astype('float32')
 test_norm = test.astype('float32')
 # normalize to range 0-1
 train_norm = train_norm / 255.0
 test_norm = test_norm / 255.0
 # return normalized images
 return train_norm, test_norm

# define cnn model
def define_model():
 model = Sequential()
 model.add(Conv2D(32, (3, 3), activation='relu', kernel_initializer='he_uniform', padding='same', input_shape=(32, 32, 3)))
 model.add(Conv2D(32, (3, 3), activation='relu', kernel_initializer='he_uniform', padding='same'))
 model.add(MaxPooling2D((2, 2)))
 model.add(Conv2D(64, (3, 3), activation='relu', kernel_initializer='he_uniform', padding='same'))
 model.add(Conv2D(64, (3, 3), activation='relu', kernel_initializer='he_uniform', padding='same'))
 model.add(MaxPooling2D((2, 2)))
 model.add(Conv2D(128, (3, 3), activation='relu', kernel_initializer='he_uniform', padding='same'))
 model.add(Conv2D(128, (3, 3), activation='relu', kernel_initializer='he_uniform', padding='same'))
 model.add(MaxPooling2D((2, 2)))
 model.add(Flatten())
 model.add(Dense(128, activation='relu', kernel_initializer='he_uniform'))
 model.add(Dense(10, activation='softmax'))
 # compile model
 opt = SGD(lr=0.001, momentum=0.9)
 model.compile(optimizer=opt, loss='categorical_crossentropy', metrics=['accuracy'])
 return model

# run the test harness for evaluating a model
def run_test_harness():
 # load dataset
 trainX, trainY, testX, testY = load_dataset()
 # prepare pixel data
 trainX, testX = prep_pixels(trainX, testX)
 # define model
 model = define_model()
 # fit model
 model.fit(trainX, trainY, epochs=50, batch_size=64, verbose=1)
 # save model
 model.save('final_model.h5')

# entry point, run the test harness
run_test_harness()

#Testing the fake pictures
#We load the fitted CIFAR10 classification model and
#see what classes are predicted by the GAN generated images for the first image of the ten rows
import numpy as np
class_names =['Airplane', 'Automobile', 'Bird', 'Cat', 'Deer', 'Dog', 'Frog', 'Horse', 'Ship', 'Truck']
cifar10_model = load_model('/content/final_model.h5')
pyplot.imshow(X[0, :, :])
pyplot.show()
#Here we show the actual predicted class values for the ten possible categories.
print(cifar10_model.predict(X[0, :, :].reshape((1,32,32,3))))
print(class_names[np.argmax(cifar10_model.predict(X[0, :, :].reshape((1,32,32,3))))])
pyplot.imshow(X[10, :, :])
pyplot.show()
print(class_names[np.argmax(cifar10_model.predict(X[10, :, :].reshape((1,32,32,3))))])
pyplot.imshow(X[20, :, :])
pyplot.show()
print(class_names[np.argmax(cifar10_model.predict(X[20, :, :].reshape((1,32,32,3))))])
pyplot.imshow(X[30, :, :])
pyplot.show()
print(class_names[np.argmax(cifar10_model.predict(X[30, :, :].reshape((1,32,32,3))))])
pyplot.imshow(X[40, :, :])
pyplot.show()
print(class_names[np.argmax(cifar10_model.predict(X[40, :, :].reshape((1,32,32,3))))])
pyplot.imshow(X[50, :, :])
pyplot.show()
print(class_names[np.argmax(cifar10_model.predict(X[50, :, :].reshape((1,32,32,3))))])
pyplot.imshow(X[60, :, :])
pyplot.show()
print(class_names[np.argmax(cifar10_model.predict(X[60, :, :].reshape((1,32,32,3))))])
pyplot.imshow(X[70, :, :])
pyplot.show()
print(class_names[np.argmax(cifar10_model.predict(X[70, :, :].reshape((1,32,32,3))))])
pyplot.imshow(X[80, :, :])
pyplot.show()
print(class_names[np.argmax(cifar10_model.predict(X[80, :, :].reshape((1,32,32,3))))])
pyplot.imshow(X[90, :, :])
pyplot.show()
print(class_names[np.argmax(cifar10_model.predict(X[90, :, :].reshape((1,32,32,3))))])

# Indices of the top 5 images
top_5_indices = [5, 15, 25, 35, 45]  # Adjust these indices based on your preference

# Function to display predicted class names and actual class numerical scores
def display_prediction_info(index):
    fake_image = X[index, :, :]
    fake_image = fake_image.reshape((1, 32, 32, 3))

    # Display the fake image
    pyplot.imshow(fake_image[0])
    pyplot.show()

    # Predict the class probabilities
    predicted_probs = cifar10_model.predict(fake_image)

    # Get the predicted class index
    predicted_class_index = np.argmax(predicted_probs)

    # Get the predicted class name
    predicted_class_name = class_names[predicted_class_index]

    # Display the predicted class name
    print(predicted_class_name)

    # Display the actual class numerical scores
    print(predicted_probs)

# Display prediction info for the top 5 images
for index in top_5_indices:
    display_prediction_info(index)

"""# **Question 3 **

Yes the 5 images that I selected have cvalues scores larger than 0.5

"""

deer_indices = [i for i in range(100) if class_names[np.argmax(cifar10_model.predict(X[i, :, :].reshape((1, 32, 32, 3))))] == 'Deer']
bird_indices = [i for i in range(100) if class_names[np.argmax(cifar10_model.predict(X[i, :, :].reshape((1, 32, 32, 3))))] == 'Bird']
print("Instances of 'Deer':")
for index in deer_indices:
    display_prediction_info(index)

print("Instances of 'Bird':")
for index in bird_indices:
    display_prediction_info(index)

# Compute and display statistics for 'Deer'
deer_class_values = [cifar10_model.predict(X[i, :, :].reshape((1, 32, 32, 3)))[0] for i in deer_indices]
deer_class_values = np.array(deer_class_values)
print("\nStatistics for 'Deer':")
print("Minimum class values:", np.min(deer_class_values, axis=0))
print("Average class values:", np.mean(deer_class_values, axis=0))
print("Maximum class values:", np.max(deer_class_values, axis=0))

# Compute and display statistics for 'Bird'
bird_class_values = [cifar10_model.predict(X[i, :, :].reshape((1, 32, 32, 3)))[0] for i in bird_indices]
bird_class_values = np.array(bird_class_values)
print("\nStatistics for 'Bird':")
print("Minimum class values:", np.min(bird_class_values, axis=0))
print("Average class values:", np.mean(bird_class_values, axis=0))
print("Maximum class values:", np.max(bird_class_values, axis=0))

"""# **Output for 100 instanaces for Bird and deer **

Statistics for 'Deer':
Minimum class values: [5.9087278e-17 1.5795323e-17 4.2748349e-10 1.6561438e-10 4.1336089e-01
 3.3522369e-16 7.5576168e-10 7.7125037e-08 3.2371346e-17 3.4745203e-22]
Average class values: [9.3996816e-04 2.8423339e-05 6.3671237e-03 7.5144701e-02 8.5386670e-01
 1.0516710e-02 1.7524216e-02 3.4002710e-02 1.3591554e-03 2.5036582e-04]
Maximum class values: [1.1140602e-02 1.9087885e-04 3.8009550e-02 3.7893724e-01 9.9999940e-01
 9.7756326e-02 2.1432857e-01 4.0435696e-01 1.0861586e-02 1.7719945e-03]


 Statistics for 'Bird':
Minimum class values: [2.5065946e-13 1.0200353e-13 6.1045349e-01 4.4723171e-07 1.1384433e-09
 8.6368503e-09 3.3642027e-09 1.9623185e-09 1.1121769e-10 4.2175381e-11]
Average class values: [1.3499348e-02 9.0889046e-03 9.0081918e-01 6.3559314e-04 3.2988700e-04
 6.6494714e-03 9.0834973e-03 3.2167398e-05 5.8010790e-02 1.8512629e-03]
Maximum class values: [9.4214387e-02 6.3520320e-02 9.9988794e-01 3.1431394e-03 2.1297580e-03
 4.2712927e-02 5.0405383e-02 1.5570059e-04 3.8862354e-01 1.2717587e-02]

"""

average_class_values = np.mean(cifar10_model.predict(X), axis=1)

top_indices = np.argsort(-average_class_values, axis=0)[:10]

print("Instances with the highest average class values:")
for index in top_indices:
    display_prediction_info(index)

# Compute and display statistics for instances with the highest average class values
top_class_values = cifar10_model.predict(X[top_indices, :, :, :])
print("\nStatistics for instances with the highest average class values:")
print("Minimum class values:", np.min(top_class_values, axis=0))
print("Average class values:", np.mean(top_class_values, axis=0))
print("Maximum class values:", np.max(top_class_values, axis=0))

"""# **Output for the highest average class value relative to all other classes**

Statistics for instances with the highest average class values:
Minimum class values: [3.3857528e-12 1.7554664e-12 5.9361471e-10 1.1841529e-05 1.4674852e-10
 5.4076240e-14 6.9086925e-10 9.8219307e-17 5.5468935e-15 9.0782402e-21]
Average class values: [0.15348296 0.05809956 0.00934189 0.1474109  0.17177127 0.04930736
 0.20634314 0.11175827 0.08135864 0.01112607]
Maximum class values: [0.9992441  0.57918954 0.04843779 0.9985428  0.8576718  0.393635
 0.9979463  0.99810445 0.8029501  0.10981598]

"""