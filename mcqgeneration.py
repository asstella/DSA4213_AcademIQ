# Import RAKE
import RAKE
import operator
import sense2vec
from sense2vec import Sense2Vec
import collections
from collections import OrderedDict
# import Cython
# import transformers
# from transformers import T5Tokenizer, T5ForConditionalGeneration

s2v = Sense2Vec().from_disk("../DSA4213/s2v_reddit_2015_md/s2v_old")

# Rake setup with stopword directory
import urllib.request
urllib.request.urlretrieve("https://raw.githubusercontent.com/zelandiya/RAKE-tutorial/master/data/stoplists/SmartStoplist.txt", "SmartStoplist.txt")
stop_dir = "SmartStoplist.txt"
rake_object = RAKE.Rake(stop_dir)
# Sample text to test RAKE
text = """Google quietly rolled out a new way for Android users to listen to podcasts and subscribe to shows they like, and it already works on your phone. Podcast production company Pacific Content got the exclusive on it.This text is taken from Google news."""

# Extract keywords
keywords = rake_object.run(text)
print ("keywords: ", keywords)


def sense2vec_get_words(word,s2v):
    output = []
    word = word.lower()
    word = word.replace(" ", "_")

    sense = s2v.get_best_sense(word)
    most_similar = s2v.most_similar(sense, n=20)

    # print ("most_similar ",most_similar)

    for each_word in most_similar:
        append_word = each_word[0].split("|")[0].replace("_", " ").lower()
        if append_word.lower() != word:
            output.append(append_word.title())

    out = list(OrderedDict.fromkeys(output))
    return out

word = "Google"
distractors = sense2vec_get_words(word,s2v)

print ("Distractors for ",word, " : ", distractors)

# question_model = T5ForConditionalGeneration.from_pretrained("../DSA4213/tf_model.h5")
# question_tokenizer = T5Tokenizer.from_pretrained("../DSA4213/tf_model.h5")
# question_model = question_model.to(device)

# def get_question(context,answer,model,tokenizer):
#   text = "context: {} answer: {}".format(context,answer)
#   encoding = tokenizer.encode_plus(text,max_length=384, pad_to_max_length=False,truncation=True, return_tensors="pt").to(device)
#   input_ids, attention_mask = encoding["input_ids"], encoding["attention_mask"]

#   outs = model.generate(input_ids=input_ids,
#                                   attention_mask=attention_mask,
#                                   early_stopping=True,
#                                   num_beams=5,
#                                   num_return_sequences=1,
#                                   no_repeat_ngram_size=2,
#                                   max_length=72)


#   dec = [tokenizer.decode(ids,skip_special_tokens=True) for ids in outs]


#   Question = dec[0].replace("question:","")
#   Question= Question.strip()
#   return Question