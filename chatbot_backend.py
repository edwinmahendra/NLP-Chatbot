import aiml
import os

import re
from collections import Counter

from flask import Flask, render_template, request, jsonify
from flask_cors import CORS


class Bot:
    def __init__(self, aiml_kernel=None):
        self.kernel = aiml_kernel if aiml_kernel else aiml.Kernel()
        self._learn_aiml()

    def _learn_aiml(self):
        self.kernel.learn("start.xml")
        self.kernel.respond("KFC")
        self.kernel.saveBrain("kbot.bot")

    def get_response(self, pesan):
        response = self.kernel.respond(pesan)
        return response if response else "Mohon maaf, saya tidak memahami pesan anda"
    
class TextCorrection:
    def __init__(self, corpus):
        self.WORDS = Counter(self.words(open(corpus).read()))

    def words(self, text):
        return re.findall(r'\w+', text.lower())

    def P(self, word, N=None):
        N = N if N else sum(self.WORDS.values())
        return self.WORDS[word] / N

    def correction(self, word):
        return max(self.candidates(word), key=self.P)

    def candidates(self, word):
        return (self.known([word]) or self.known(self.edits1(word)) or self.known(self.edits2(word)) or [word])

    def known(self, words):
        return set(w for w in words if w in self.WORDS)

    def edits1(self, word):
        letters    = 'abcdefghijklmnopqrstuvwxyz'
        splits     = [(word[:i], word[i:])    for i in range(len(word) + 1)]
        deletes    = [L + R[1:]               for L, R in splits if R]
        transposes = [L + R[1] + R[0] + R[2:] for L, R in splits if len(R)>1]
        replaces   = [L + c + R[1:]           for L, R in splits if R for c in letters]
        inserts    = [L + c + R               for L, R in splits for c in letters]
        return set(deletes + transposes + replaces + inserts)

    def edits2(self, word):
        return (e2 for e1 in self.edits1(word) for e2 in self.edits1(e1))

def create_app():
    app = Flask(__name__)
    CORS(app)
    bot = Bot()
    text_correction = TextCorrection('corpus.txt')

    @app.route("/")
    def home():
        return render_template("base.html")

    @app.route("/predict", methods=['POST'])
    def send_message():
        pesan = request.get_json()["message"]
        print(pesan)
        
        # Correct each word in the message
        pesanFix = " ".join(text_correction.correction(word) for word in pesan.split())

        print("Hasil Koreksi : " + pesanFix)

        # Get bot's response and split it into words
        response_words = bot.get_response(pesanFix).split()

        # Substitute "^" with "<br>" in the response
        response_bot = " ".join("<br>" if word == "^" else word for word in response_words)

        # Return the corrected response
        return jsonify({"message": response_bot.strip()})

    return app

if __name__ == "__main__":
    create_app().run(debug=True, port=5001)