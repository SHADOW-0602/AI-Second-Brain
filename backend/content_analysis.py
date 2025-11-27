import re
from typing import List, Dict, Any
from collections import Counter
import spacy
from datetime import datetime

try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    nlp = None

class ContentAnalyzer:
    def __init__(self):
        self.nlp = nlp
    
    def extract_entities(self, text: str) -> Dict[str, List[str]]:
        """Extract named entities from text"""
        if not self.nlp:
            return {"entities": [], "dates": [], "organizations": [], "persons": []}
        
        doc = self.nlp(text)
        entities = {
            "persons": [ent.text for ent in doc.ents if ent.label_ == "PERSON"],
            "organizations": [ent.text for ent in doc.ents if ent.label_ == "ORG"],
            "dates": [ent.text for ent in doc.ents if ent.label_ == "DATE"],
            "locations": [ent.text for ent in doc.ents if ent.label_ in ["GPE", "LOC"]],
            "money": [ent.text for ent in doc.ents if ent.label_ == "MONEY"],
            "technologies": [ent.text for ent in doc.ents if ent.label_ in ["PRODUCT", "EVENT"]]
        }
        return entities
    
    def extract_keywords(self, text: str, top_k: int = 10) -> List[Dict[str, Any]]:
        """Extract key terms and phrases"""
        if not self.nlp:
            # Fallback to simple word frequency
            words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
            word_freq = Counter(words)
            return [{"term": word, "frequency": freq, "importance": freq/len(words)} 
                   for word, freq in word_freq.most_common(top_k)]
        
        doc = self.nlp(text)
        
        # Extract noun phrases and important words
        keywords = []
        for token in doc:
            if (token.pos_ in ["NOUN", "PROPN", "ADJ"] and 
                not token.is_stop and 
                not token.is_punct and 
                len(token.text) > 2):
                keywords.append(token.lemma_.lower())
        
        # Extract noun phrases
        noun_phrases = [chunk.text.lower() for chunk in doc.noun_chunks if len(chunk.text) > 3]
        keywords.extend(noun_phrases)
        
        keyword_freq = Counter(keywords)
        total_keywords = len(keywords)
        
        return [{"term": term, "frequency": freq, "importance": freq/total_keywords} 
               for term, freq in keyword_freq.most_common(top_k)]
    
    def generate_summary(self, text: str, max_sentences: int = 3) -> str:
        """Generate extractive summary"""
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 20]
        
        if len(sentences) <= max_sentences:
            return text
        
        # Simple scoring based on sentence length and position
        scored_sentences = []
        for i, sentence in enumerate(sentences):
            score = len(sentence.split())  # Word count
            if i < 3:  # Boost early sentences
                score *= 1.5
            scored_sentences.append((score, sentence))
        
        # Select top sentences
        scored_sentences.sort(reverse=True)
        top_sentences = [sent for _, sent in scored_sentences[:max_sentences]]
        
        return '. '.join(top_sentences) + '.'
    
    def generate_questions(self, text: str, num_questions: int = 5) -> List[str]:
        """Generate questions from text content"""
        if not self.nlp:
            return ["What is the main topic of this document?"]
        
        doc = self.nlp(text)
        questions = []
        
        # Extract entities for question generation
        entities = self.extract_entities(text)
        
        # Generate questions based on entities
        if entities["persons"]:
            questions.append(f"Who is {entities['persons'][0]}?")
        
        if entities["organizations"]:
            questions.append(f"What is {entities['organizations'][0]}?")
        
        if entities["dates"]:
            questions.append(f"What happened on {entities['dates'][0]}?")
        
        # Generate questions from key concepts
        keywords = self.extract_keywords(text, 3)
        for keyword in keywords:
            questions.append(f"What is {keyword['term']}?")
            questions.append(f"How does {keyword['term']} work?")
        
        # Add generic questions
        questions.extend([
            "What is the main purpose of this document?",
            "What are the key takeaways?",
            "How can this information be applied?"
        ])
        
        return questions[:num_questions]
    
    def analyze_content_gaps(self, all_texts: List[str]) -> Dict[str, Any]:
        """Identify knowledge gaps in the content"""
        all_keywords = []
        all_entities = {"persons": [], "organizations": [], "technologies": []}
        
        for text in all_texts:
            keywords = self.extract_keywords(text, 20)
            all_keywords.extend([kw["term"] for kw in keywords])
            
            entities = self.extract_entities(text)
            for key in all_entities:
                all_entities[key].extend(entities.get(key, []))
        
        keyword_freq = Counter(all_keywords)
        
        # Identify potential gaps (mentioned infrequently)
        rare_topics = [term for term, freq in keyword_freq.items() if freq == 1]
        common_topics = [term for term, freq in keyword_freq.most_common(10)]
        
        return {
            "rare_topics": rare_topics[:10],
            "common_topics": common_topics,
            "entity_coverage": {k: len(set(v)) for k, v in all_entities.items()},
            "suggested_research": [f"More information needed about {topic}" for topic in rare_topics[:5]]
        }

content_analyzer = ContentAnalyzer()