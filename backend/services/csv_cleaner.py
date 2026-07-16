"""
CSV Cleaner - Deep cleaning for social media data
Removes duplicates, noise, spam, and irrelevant content
"""

import pandas as pd
import numpy as np
from pathlib import Path
import re
from datetime import datetime
import hashlib


class CSVCleaner:
    def __init__(self, csv_path, topic_name):
        self.csv_path = csv_path
        self.topic_name = topic_name
        self.df = None
        self.stats = {
            'original_count': 0,
            'after_duplicates': 0,
            'after_relevance': 0,
            'after_spam': 0,
            'after_bots': 0,
            'final_count': 0
        }
    
    def load_data(self):
        """Load CSV file"""
        print(f"📂 Loading: {self.csv_path}")
        self.df = pd.read_csv(self.csv_path)
        self.stats['original_count'] = len(self.df)
        print(f"✅ Loaded {len(self.df)} records")
        return self
    
    def remove_duplicates(self):
        """Remove exact and near duplicates"""
        print("\n🔍 Step 1: Removing duplicates...")
        
        # Create content hash for near-duplicate detection
        def create_hash(text):
            if pd.isna(text):
                return None
            # Normalize: lowercase, remove extra spaces
            normalized = re.sub(r'\s+', ' ', str(text).lower().strip())
            return hashlib.md5(normalized.encode()).hexdigest()
        
        self.df['content_hash'] = self.df['Text'].apply(create_hash)
        
        # Remove exact duplicates
        before = len(self.df)
        self.df = self.df.drop_duplicates(subset=['content_hash'], keep='first')
        removed = before - len(self.df)
        
        self.stats['after_duplicates'] = len(self.df)
        print(f"  ✅ Removed {removed} duplicate posts")
        print(f"  📊 Remaining: {len(self.df)} records")
        
        return self
    
    def filter_relevance(self):
        """Keep only content relevant to the topic - preserves post-comment relationships"""
        print(f"\n🎯 Step 2: Filtering for '{self.topic_name}' relevance...")

        # Create search patterns
        topic_words = self.topic_name.lower().split()
        patterns = [
            self.topic_name.lower(),
            self.topic_name.replace(' ', '').lower(),
            ''.join(topic_words),
            ' '.join(topic_words)
        ]

        # Check if text contains topic
        def is_relevant(text):
            if pd.isna(text):
                return False
            text_lower = str(text).lower()
            return any(pattern in text_lower for pattern in patterns)

        before = len(self.df)

        # Mark relevance for all records
        self.df['is_relevant'] = self.df['Text'].apply(is_relevant)

        # IMPORTANT: Keep comments even if they don't mention the topic
        # A comment is relevant if it's a comment (Type == 'comment')
        # We'll keep all comments because they're related to posts
        if 'Type' in self.df.columns:
            # Keep all comments regardless of content
            # Keep posts only if they mention the topic
            self.df['keep'] = (self.df['Type'] == 'comment') | (self.df['is_relevant'] == True)
        else:
            # If no Type column, use relevance only
            self.df['keep'] = self.df['is_relevant']

        self.df = self.df[self.df['keep'] == True].copy()
        self.df = self.df.drop(columns=['keep'])

        removed = before - len(self.df)

        self.stats['after_relevance'] = len(self.df)
        print(f"  ✅ Removed {removed} irrelevant posts (kept all comments)")
        print(f"  📊 Remaining: {len(self.df)} records")

        return self
    
    def remove_spam(self):
        """Remove spam and promotional content"""
        print("\n🚫 Step 3: Removing spam...")
        
        spam_indicators = [
            r'click here', r'buy now', r'limited time', r'act now',
            r'http://bit\.ly', r'http://tinyurl', r'🎁.*🎁', 
            r'💰.*💰', r'free.*click', r'win.*prize',
            r'⬇️.*⬇️.*⬇️', # Multiple down arrows
        ]
        
        def is_spam(text):
            if pd.isna(text):
                return False
            text_lower = str(text).lower()
            return any(re.search(pattern, text_lower) for pattern in spam_indicators)
        
        before = len(self.df)
        self.df = self.df[~self.df['Text'].apply(is_spam)].copy()
        removed = before - len(self.df)
        
        self.stats['after_spam'] = len(self.df)
        print(f"  ✅ Removed {removed} spam posts")
        print(f"  📊 Remaining: {len(self.df)} records")
        
        return self
    
    def remove_bots(self):
        """Remove bot-generated content"""
        print("\n🤖 Step 4: Removing bot content...")
        
        # Bot indicators
        def is_bot(row):
            text = str(row.get('Text', ''))
            username = str(row.get('Username', ''))
            
            # Check for bot patterns
            bot_patterns = [
                r'bot$', r'^bot_', r'_bot_', r'automated',
                r'^\d+$',  # Username is just numbers
            ]
            
            # Repetitive content
            if len(text) > 0:
                words = text.split()
                if len(words) > 5:
                    unique_ratio = len(set(words)) / len(words)
                    if unique_ratio < 0.3:  # Less than 30% unique words
                        return True
            
            # Bot username
            username_lower = username.lower()
            if any(re.search(pattern, username_lower) for pattern in bot_patterns):
                return True
            
            return False
        
        before = len(self.df)
        self.df = self.df[~self.df.apply(is_bot, axis=1)].copy()
        removed = before - len(self.df)
        
        self.stats['after_bots'] = len(self.df)
        print(f"  ✅ Removed {removed} bot posts")
        print(f"  📊 Remaining: {len(self.df)} records")

        return self

    def enrich_data(self):
        """Add useful metadata"""
        print("\n📊 Step 5: Enriching data...")

        # Add text length
        self.df['text_length'] = self.df['Text'].str.len()

        # Add word count
        self.df['word_count'] = self.df['Text'].str.split().str.len()

        # Add has_url flag
        self.df['has_url'] = self.df['Text'].str.contains(r'http', na=False)

        # Add has_mention flag
        self.df['has_mention'] = self.df['Text'].str.contains(r'@\w+', na=False)

        # Add has_hashtag flag
        self.df['has_hashtag'] = self.df['Text'].str.contains(r'#\w+', na=False)

        # Extract mentioned users count
        self.df['mention_count'] = self.df['Text'].str.findall(r'@\w+').str.len()

        # Extract hashtag count
        self.df['hashtag_count'] = self.df['Text'].str.findall(r'#\w+').str.len()

        print("  ✅ Added metadata columns")

        return self

    def clean_text(self):
        """Clean and normalize text"""
        print("\n🧹 Step 6: Cleaning text...")

        def clean_single_text(text):
            if pd.isna(text):
                return text

            text = str(text)
            # Remove extra whitespace
            text = re.sub(r'\s+', ' ', text)
            # Remove leading/trailing whitespace
            text = text.strip()

            return text

        self.df['Text'] = self.df['Text'].apply(clean_single_text)

        print("  ✅ Text cleaned")

        return self

    def save_clean_data(self, output_dir='data/cleanCSV'):
        """Save cleaned data"""
        print(f"\n💾 Saving cleaned data...")

        # Create output directory
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # Generate filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        topic_slug = self.topic_name.replace(' ', '_')
        filename = f"CLEAN_{topic_slug}_{timestamp}.csv"
        filepath = output_path / filename

        # Remove temporary columns
        columns_to_drop = ['content_hash', 'is_relevant']
        self.df = self.df.drop(columns=[col for col in columns_to_drop if col in self.df.columns])

        # Save
        self.df.to_csv(filepath, index=False)

        self.stats['final_count'] = len(self.df)

        print(f"  ✅ Saved: {filepath}")
        print(f"  📊 Final count: {len(self.df)} records")

        return str(filepath)

    def print_summary(self):
        """Print cleaning summary"""
        print("\n" + "="*80)
        print("📊 CLEANING SUMMARY")
        print("="*80)

        print(f"\n📥 Input:")
        print(f"  Original records: {self.stats['original_count']}")

        print(f"\n🔄 Cleaning Steps:")
        print(f"  After removing duplicates: {self.stats['after_duplicates']} "
              f"(-{self.stats['original_count'] - self.stats['after_duplicates']})")
        print(f"  After relevance filter: {self.stats['after_relevance']} "
              f"(-{self.stats['after_duplicates'] - self.stats['after_relevance']})")
        print(f"  After spam removal: {self.stats['after_spam']} "
              f"(-{self.stats['after_relevance'] - self.stats['after_spam']})")
        print(f"  After bot removal: {self.stats['after_bots']} "
              f"(-{self.stats['after_spam'] - self.stats['after_bots']})")

        print(f"\n📤 Output:")
        print(f"  Final clean records: {self.stats['final_count']}")

        # Calculate quality improvement
        quality_pct = (self.stats['final_count'] / self.stats['original_count']) * 100
        removed_pct = 100 - quality_pct

        print(f"\n📈 Quality Metrics:")
        print(f"  Kept: {quality_pct:.1f}% ({self.stats['final_count']} records)")
        print(f"  Removed: {removed_pct:.1f}% ({self.stats['original_count'] - self.stats['final_count']} records)")

        print("\n" + "="*80)

    def clean_all(self):
        """Run all cleaning steps"""
        return (self
                .load_data()
                .remove_duplicates()
                .filter_relevance()
                .remove_spam()
                .remove_bots()
                .enrich_data()
                .clean_text())


def clean_csv(csv_path, topic_name, output_dir='data/cleanCSV'):
    """
    Main function to clean a CSV file

    Args:
        csv_path: Path to the CSV file
        topic_name: Brand/topic name to filter for
        output_dir: Where to save cleaned data

    Returns:
        Path to cleaned CSV file
    """
    cleaner = CSVCleaner(csv_path, topic_name)
    cleaner.clean_all()
    cleaner.print_summary()
    clean_path = cleaner.save_clean_data(output_dir)

    return clean_path, cleaner.df
