import tensorflow as tf
import pickle
import numpy as np
from numpy import linalg as la
from nltk.tokenize import TweetTokenizer
from django.conf import settings


class ImportGraph:
    instance = None

    @staticmethod
    def get_instance():
        if ImportGraph.instance is None:
            return ImportGraph(settings.BASE_DIR + "/Venter/ML_model/model/" + 'model.ckpt')
        else:
            return ImportGraph.instance

    def init_weight(self, shape, name):
        initial = tf.truncated_normal(shape, stddev=0.1, name=name, dtype=tf.float32)
        return tf.Variable(initial)

    def init_bias(self, shape, name):
        initial = tf.truncated_normal(shape=shape, stddev=0.1, name=name, dtype=tf.float32)
        return tf.Variable(initial)

    def __init__(self, path_to_model):
        global word_vectors
        g = tf.Graph()
        with g.as_default():
            train_attention = True
            initialize_random = False
            train_we = True

            with open(settings.BASE_DIR + str(
                    "/Venter/ML_model/dataset/dataset_mcgm_clean/word_index_map_mcgm.pickle"), "rb") as myFile:
                self.word_index_map = pickle.load(myFile, encoding='latin1')

            if not initialize_random:

                # load pre-trained word embedding.
                with open(settings.BASE_DIR + "/Venter/ML_model/dataset/dataset_mcgm_clean/word_vectors_mcgm.pickle",
                          "rb") as myFile:
                    word_vectors = pickle.load(myFile, encoding='latin1')

                word_vectors = np.asarray(word_vectors).astype(np.float32)

                for i in range(len(word_vectors) - 1):
                    word_vectors[i] /= (la.norm((word_vectors[i])))

            vocab_size = len(word_vectors)
            embedding_dim = 300
            # learning_rate = 1e-3
            # decay_factor = 0.99
            self.max_padded_sentence_length = 35
            # batch_size = 100
            # iterations = 200
            # highest_val_acc = 0
            self.last_index = len(word_vectors) - 1

            def init_weight(shape, name):
                initial = tf.truncated_normal(shape, stddev=0.1, name=name, dtype=tf.float32)
                return tf.Variable(initial)

            def init_bias(shape, name):
                initial = tf.truncated_normal(shape=shape, stddev=0.1, name=name, dtype=tf.float32)
                return tf.Variable(initial)

            if initialize_random:

                # Initial embedding initialized randomly
                embedding_init = tf.Variable(
                    tf.truncated_normal(shape=[vocab_size, embedding_dim], stddev=0.1, dtype=tf.float32),
                    trainable=train_we, name="word_embedding")

            else:

                # Initial embedding initialized by word2vec vectors
                embedding_init = tf.Variable(tf.constant(word_vectors, shape=[vocab_size, embedding_dim]),
                                             trainable=train_we, name="word_embedding")

            # config = projector.ProjectorConfig()
            # It will hold tensor of size [batch_size, max_padded_sentence_length]
            self.X = tf.placeholder(tf.int32, [None, self.max_padded_sentence_length])

            # Word embedding lookup
            word_embeddings = tf.nn.embedding_lookup(embedding_init, self.X)

            if train_attention:

                in_size = tf.shape(word_embeddings)[0]

                reshaped_w_e = tf.reshape(word_embeddings, [in_size * self.max_padded_sentence_length, embedding_dim])

                print(reshaped_w_e)

                no_of_nurons_h1 = 512
                Wa = init_weight([embedding_dim, no_of_nurons_h1], 'Wa')
                ba = init_bias([no_of_nurons_h1], 'ba')
                ya = tf.nn.relu(tf.matmul(reshaped_w_e, Wa) + ba)

                # Hidden layer of size 512
                no_of_nurons_h2 = 512
                Wa1 = init_weight([no_of_nurons_h1, no_of_nurons_h2], 'Wa1')
                ba1 = init_bias([no_of_nurons_h2], 'ba1')
                ya1 = tf.nn.relu(tf.matmul(ya, Wa1) + ba1)

                Wa2 = init_weight([no_of_nurons_h2, 1], 'Wa2')
                ba2 = init_bias([1], 'ba2')

                # Output layer of the neural network.
                ya2 = tf.matmul(ya1, Wa2) + ba2

                attention_reshaped = tf.reshape(ya2, [in_size, self.max_padded_sentence_length])

                attention_softmaxed = tf.nn.softmax(attention_reshaped)

                attention_expanded = tf.expand_dims(attention_softmaxed, axis=2)

                # Attention based weighted averaging of word vectors.
                sentence_embedding = tf.reduce_sum(tf.multiply(word_embeddings, attention_expanded), axis=1)

            else:

                # Simply Average out word embedding to create sentence embedding
                sentence_embedding = tf.reduce_mean(word_embeddings, axis=1)

            def get_batches(X, Y, bsize):
                for i in range(0, len(X) - bsize + 1, bsize):
                    indices = slice(i, i + bsize)
                    yield X[indices], Y[indices]

            input_layer_size = embedding_dim
            output_layer_size = 165

            # Hidden layer of size 1024
            no_of_nurons_h1 = 512
            W = init_weight([input_layer_size, no_of_nurons_h1], 'W')
            b = init_bias([no_of_nurons_h1], 'b')
            y = tf.nn.relu(tf.matmul(sentence_embedding, W) + b)

            # Hidden layer of size 1024
            no_of_nurons_h2 = 512
            W1 = init_weight([no_of_nurons_h1, no_of_nurons_h2], 'W1')
            b1 = init_bias([no_of_nurons_h2], 'b1')
            y1 = tf.nn.relu(tf.matmul(y, W1) + b1)

            W2 = init_weight([no_of_nurons_h2, output_layer_size], 'W2')
            b2 = init_bias([output_layer_size], 'b2')

            # Output layer of the neural network.
            y2 = tf.matmul(y1, W2) + b2

            # It will hold the true label for current batch
            self.probs = tf.nn.softmax(y2)

            init = tf.global_variables_initializer()
            self.sess = tf.Session()
            self.sess.run(init)

            saver = tf.train.Saver()

            # Restore the best model to calculate the test accuracy.
            saver.restore(self.sess, path_to_model)

    def run(self, data):
        """ Running the activation operation previously imported """
        # The 'x' corresponds to name of input placeholder
        return self.sess.run(self.probs, feed_dict={self.X: data})

    def process_query(self, line, flag):

        if flag == 1:
            tokens = TweetTokenizer().tokenize(line.strip())
        else:
            tokens = line.strip().split()
        indices = []
        clean_words = []
        for token in tokens:
            if token.strip() in self.word_index_map.keys():
                indices.append(self.word_index_map[token.strip()])
                clean_words.append(token.strip())
        if len(indices) < 100:
            indices += [self.last_index] * (self.max_padded_sentence_length - len(indices))
        else:
            return ""
        indices = np.asarray(indices)
        data = []
        data.append(indices)
        data = np.asarray(data)

        return data
