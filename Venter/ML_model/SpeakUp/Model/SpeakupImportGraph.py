import tensorflow as tf
import numpy as np
from nltk.tokenize import TweetTokenizer
import gensim
import os
from django.conf import settings


class ImportGraph():
    instance = None

    @staticmethod
    def get_instance():
        if ImportGraph.instance is None:
            return ImportGraph(settings.BASE_DIR + "/Venter/ML_model/SpeakUp/Model/model.ckpt")
        else:
            return ImportGraph.instance

    def __init__(self, path_to_model):
        g = tf.Graph()
        with g.as_default():
            model = gensim.models.Word2Vec.load(
                os.path.join(settings.BASE_DIR, "Venter", "ML_model", "SpeakUp", "dataset", "speakup",
                             "word2vec_speakup_min_count_5_mix.model"))
            self.vecs = model.wv
            self.words = set()
            for word, vocab_obj in self.vecs.vocab.items():
                self.words.add(word)
            embedding_dim = 300

            def init_weight(shape, name):
                initial = tf.truncated_normal(shape, stddev=0.1, name=name, dtype=tf.float32)
                return tf.Variable(initial)

            def init_bias(shape, name):
                initial = tf.truncated_normal(shape=shape, stddev=0.1, name=name, dtype=tf.float32)
                return tf.Variable(initial)

            # It will hold tensor of size [batch_size, max_padded_sentence_length]
            self.X = tf.placeholder(tf.float32, [None, embedding_dim])

            def get_batches(X, Y, bsize):
                for i in range(0, len(X) - bsize + 1, bsize):
                    indices = slice(i, i + bsize)
                    yield X[indices], Y[indices]

            input_layer_size = embedding_dim
            output_layer_size = 14

            # Hidden layer of size 1024
            no_of_nurons_h2 = 128
            W1 = init_weight([input_layer_size, no_of_nurons_h2], 'W1')
            b1 = init_bias([no_of_nurons_h2], 'b1')
            y1 = tf.nn.relu(tf.matmul(self.X, W1) + b1)

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

    def get_clean_complaint_text_words(self, complaint_text):
        tknzr = TweetTokenizer()
        tokens = tknzr.tokenize(complaint_text.strip().lower())
        complaint_text_tokens = []
        for token in tokens:
            if token.strip() in self.words:
                complaint_text_tokens.append(token.strip())
        return complaint_text_tokens

    def process_query(self, line):
        tokens = self.get_clean_complaint_text_words(line)
        vec = np.zeros(shape=300)
        for token in tokens:
            vec += self.vecs.word_vec(token)
        if len(tokens) != 0:
            vec /= len(tokens)
        data = np.asarray(vec)
        return [data]
