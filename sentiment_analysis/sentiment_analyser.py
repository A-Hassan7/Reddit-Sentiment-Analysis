import re
import statistics
import string
from pathlib import Path

import nltk
import pandas as pd
from nltk import FreqDist, WordNetLemmatizer
from nltk.corpus import stopwords, wordnet
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from nltk.tag import pos_tag
from nltk.tokenize import sent_tokenize, word_tokenize
from wordcloud import WordCloud

from config import Loggers
from sentiment_analysis._analyser import additional_stopwords, custom_lexicon

# Set path to nltk data 
nltk.data.path.append(Path('sentiment_analysis/nltk_data'))

class SentimentAnalyser:
    """
    Uses the Python Natural Language Toolkit (NLTK) to perform sentiment
    analysis on language data.
    """

    def __init__(self):
        self.logger = Loggers.console
        
    def _clean_text(self, text, stop_words, search_patterns):
        """
        Removes unwanted tokens based on RegEx search patters using
        python RegEx library.

        Args:
            text (str): text to clean
            stop_words (list): list of stop words to remove
            search_patterns (list): list of python RegEx search patters to remove
        """
        
        # substitute search pattern matches
        for pattern in search_patterns:
            text = re.sub(pattern, "", text)
        
        # tokenize text
        tokens = word_tokenize(text)
        
        # remove punctuation, stopwords
        cleaned_tokens = []
        for token in tokens:

            # skip unwanted tokens
            if (not token 
                    or token in string.punctuation
                    or token.lower() in stop_words):
                continue

            cleaned_tokens.append(token.lower())

        return cleaned_tokens
    
    def _simplify_tag(self, tag):
        """
        Attempts to map tags to wordnet POS tags for the
        wordnet Lemmatizer
        
        Args:
            tag (str): string tag
        """

        if tag.startswith('J'):
            return wordnet.ADJ
        elif tag.startswith('V'):
            return wordnet.VERB
        elif tag.startswith('N'):
            return wordnet.NOUN
        elif tag.startswith('R'):
            return wordnet.ADV
        else:
            return wordnet.NOUN
        
    def _lemmatize_tokens(self, tagged_tokens):
        """
        Ruturns root words from tagged tokens e.g. ('running', 'verb').
        Lemmmatizing is a Normalising function that uses the words context
        i.e. noun, verb, adverb etc. to find the words conocial form or 
        root word.

        ex: ('running', 'verb') --> 'run'

        Args:
            tagged_tokens (list): list of tuples like (word, tag)
        """
        
        lemmatizer = WordNetLemmatizer()
        
        lemmatized_sentence = []
        for word, tag in tagged_tokens:
            
            # simplify tag for wordnet lemmatizer
            pos = self._simplify_tag(tag)
            
            # lemmatize the word
            lemmatized_word = lemmatizer.lemmatize(word, pos)
            lemmatized_sentence.append(lemmatized_word)

        return lemmatized_sentence
    
    def _flatten_preprocessed_text(self, preprocessed_text):
        """
        Flatten preprocessed_text into a 1D array
        """
        return [text for entry in preprocessed_text for sublist in entry for text in sublist]
    
    def _customize_vader(self, vader):
        """
        Updates Vader Lexicon with custom words from financial jargon
        """
        vader.lexicon |= custom_lexicon.financial_jargon
        return vader
    
    def preprocess_text(self, text_list: list) -> list:
        """
        Preprocess text for analysis by cleaning, tagging and lemmatising.
        
        Args:
            text_list (list):
                List of strings containing text to preprocessed
                ex: [
                        ['This is a long reddit post'],
                        ['This is another long reddit post']
                    ]
        """
        
        self.logger.info('Preprocessing text')
        
        # RegEx search patterns to remove
        punctuation_pattern = "[^-9A-Za-z ]"
        url_pattern = "http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+#]|[!*\(\),]|" \
                       "(?:%[0-9a-fA-F][0-9a-fA-F]))+"
        search_patterns = [url_pattern, punctuation_pattern]
        
        # add custom stop words
        stop_words = stopwords.words('english') + additional_stopwords.words
        
        preprocessed_text = []
        for text in text_list:
            
            # split text into sentences
            preprocessed_sentences = []
            sentences = sent_tokenize(text)
            for sentence in sentences:
                
                # remove unwanted text
                clean_sentence = self._clean_text(
                    text=sentence,
                    stop_words=stop_words,
                    search_patterns=search_patterns
                )

                # lemmatize text
                tagged_sentence = pos_tag(clean_sentence)
                lemmatized_sentence = self._lemmatize_tokens(tagged_sentence)
            
                preprocessed_sentences.append(lemmatized_sentence)
            
            preprocessed_text.append(preprocessed_sentences)
            
        return preprocessed_text
    
    def create_wordcloud(
        self,
        preprocessed_text: list,
        max_words: int=30,
        colormap: str=None, 
        background_color: str='white'
        ) -> WordCloud:
        """
        Creates a wordcloud image from preprocessed text

        Args:
            preprocesed_text (list): 
                text that has been preprocessed by the preprocess_text function
        """
        
        self.logger.info('Creating wordcloud')
        
        # create frequency distribution dictionary
        fd = self.create_freqdist(preprocessed_text, max_words=max_words)
        fd = fd.set_index('word')['count'].to_dict()
        
        # create wordcloud
        wordcloud = WordCloud(
            max_words=max_words,
            colormap=colormap,
            background_color=background_color
        )
        
        return wordcloud.fit_words(fd)
        
    def create_freqdist(
        self, 
        preprocessed_text: list,
        max_words: int=30
        ) -> pd.DataFrame:
        """
        Create frequency distribution of words in text
        
        Args:
            preprocesed_text (list): 
                text that has been preprocessed by the preprocess_text function
        """
        
        self.logger.info('creating frequency distribution')
        
        # flatten preprocessed_text list
        flattened_text = self._flatten_preprocessed_text(preprocessed_text)
        
        # create distribution and sort by count
        fd = FreqDist(flattened_text)
        dist = pd.DataFrame.from_records(
                data=fd.most_common(),
                columns=['word', 'count']
        ).sort_values(by='count', ascending=False)
        
        return dist[:max_words] if max_words else dist

    def sentiment_score(
        self,
        preprocessed_text: list,
        customise_vader: bool=True
        ) -> list:
        """
        Analyse preprocessed_text for sentiment using nltk's pretrained
        vader sentiment analyser.
        
        Args:
            preprocessed_text (list):
                text that has been preprocessed by the preprocess_text function
            customize_vader (bool): 
                Adds custom financial jargon to vader lexicon of True
        """
        
        self.logger.info('generating sentiment scores')
        
        # Initialise vader sentiment analyser
        vader = SentimentIntensityAnalyzer()
        vader = self._customize_vader(vader) if customise_vader else vader
        
        # calculate sentiment for each item
        item_scores = []
        for item in preprocessed_text:
            
            # calculate sentiment for each sentence in item
            sentence_scores = []
            for sentence in item:

                # join sentence list and get compound sentiment
                sentence = ' '.join(sentence)
                score = vader.polarity_scores(sentence)['compound']
                
                sentence_scores.append(score)
            
            # take mean sentement of all sentences
            item_scores.append(statistics.mean(sentence_scores))
                
        return item_scores
