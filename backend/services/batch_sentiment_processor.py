"""
Batch Sentiment Processor
Processes sentiment and emotion for multiple platforms in batch mode
"""

import pandas as pd
import logging
from typing import List, Dict, Any
from pathlib import Path
import asyncio
from datetime import datetime

logger = logging.getLogger(__name__)


class BatchSentimentProcessor:
    """
    Process sentiment and emotion analysis in batch mode for multiple platforms
    """
    
    def __init__(self, sentiment_analyzer=None, emotion_analyzer=None):
        """
        Initialize batch processor
        
        Args:
            sentiment_analyzer: Sentiment analysis model
            emotion_analyzer: Emotion analysis model
        """
        self.sentiment_analyzer = sentiment_analyzer
        self.emotion_analyzer = emotion_analyzer
        logger.info("✅ Batch Sentiment Processor initialized")
    
    async def process_all_platforms(
        self,
        raw_data_dir: str = "data/raw",
        output_dir: str = "data/processed"
    ) -> Dict[str, Any]:
        """
        Process sentiment for all platforms in batch
        
        Args:
            raw_data_dir: Directory containing raw CSV files
            output_dir: Directory to save processed files
            
        Returns:
            Summary of processing results
        """
        try:
            logger.info("🤖 Starting batch sentiment processing...")
            
            raw_path = Path(raw_data_dir)
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            
            # Find all raw CSV files
            csv_files = list(raw_path.glob("*.csv"))
            
            if not csv_files:
                logger.warning(f"⚠️ No CSV files found in {raw_data_dir}")
                return {"status": "no_files", "processed": 0}
            
            logger.info(f"📁 Found {len(csv_files)} CSV files to process")
            
            # Process each file
            results = {}
            total_records = 0
            
            for csv_file in csv_files:
                logger.info(f"📊 Processing: {csv_file.name}")
                
                # Read CSV
                df = pd.read_csv(csv_file)
                original_count = len(df)
                
                # Process sentiment and emotion
                df_processed = await self._process_dataframe(df)
                
                # Save processed file
                output_file = output_path / csv_file.name.replace("_raw", "_sentiment")
                df_processed.to_csv(output_file, index=False)
                
                results[csv_file.stem] = {
                    "records": len(df_processed),
                    "output_file": str(output_file)
                }
                
                total_records += len(df_processed)
                logger.info(f"✅ Saved: {output_file.name} ({len(df_processed)} records)")
            
            logger.info(f"🎉 Batch processing complete! Total: {total_records} records")
            
            return {
                "status": "success",
                "files_processed": len(csv_files),
                "total_records": total_records,
                "results": results
            }
            
        except Exception as e:
            logger.error(f"❌ Batch processing failed: {e}")
            return {"status": "error", "error": str(e)}
    
    async def _process_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Process sentiment and emotion for a dataframe
        
        Args:
            df: Input dataframe
            
        Returns:
            Dataframe with sentiment and emotion columns
        """
        try:
            # Extract texts
            texts = df['Text'].fillna('').tolist()
            
            if not texts:
                return df
            
            logger.info(f"   🔍 Analyzing {len(texts)} texts...")
            
            # Process sentiment
            if self.sentiment_analyzer:
                sentiments = await self._analyze_sentiment_batch(texts)
                df['sentiment_label'] = [s['label'] for s in sentiments]
                df['sentiment_score'] = [s['score'] for s in sentiments]
            else:
                df['sentiment_label'] = 'neutral'
                df['sentiment_score'] = 0.0
            
            # Process emotion
            if self.emotion_analyzer:
                emotions = await self._analyze_emotion_batch(texts)
                df['emotion_label'] = [e['label'] for e in emotions]
                df['emotion_score'] = [e['score'] for e in emotions]
            else:
                df['emotion_label'] = 'neutral'
                df['emotion_score'] = 0.0
            
            logger.info(f"   ✅ Analysis complete")
            
            return df
            
        except Exception as e:
            logger.error(f"❌ Error processing dataframe: {e}")
            return df
    
    async def _analyze_sentiment_batch(self, texts: List[str]) -> List[Dict]:
        """Analyze sentiment for batch of texts"""
        try:
            if not self.sentiment_analyzer:
                return [{"label": "neutral", "score": 0.0} for _ in texts]

            # Truncate texts to avoid token length issues
            truncated_texts = [text[:400] if len(text) > 400 else text for text in texts]

            # Process in batch
            results = self.sentiment_analyzer(truncated_texts)

            # Extract top prediction for each text
            sentiment_results = []
            for result in results:
                if isinstance(result, list) and len(result) > 0:
                    top_result = max(result, key=lambda x: x['score'])
                    sentiment_results.append({
                        "label": top_result['label'],
                        "score": top_result['score']
                    })
                else:
                    sentiment_results.append({"label": "neutral", "score": 0.0})

            return sentiment_results

        except Exception as e:
            logger.error(f"❌ Error in sentiment batch analysis: {e}")
            return [{"label": "neutral", "score": 0.0} for _ in texts]

    async def _analyze_emotion_batch(self, texts: List[str]) -> List[Dict]:
        """Analyze emotion for batch of texts"""
        try:
            if not self.emotion_analyzer:
                return [{"label": "neutral", "score": 0.0} for _ in texts]

            # Truncate texts to avoid token length issues
            truncated_texts = [text[:400] if len(text) > 400 else text for text in texts]

            # Process in batch
            results = self.emotion_analyzer(truncated_texts)

            # Extract top prediction for each text
            emotion_results = []
            for result in results:
                if isinstance(result, list) and len(result) > 0:
                    top_result = max(result, key=lambda x: x['score'])
                    emotion_results.append({
                        "label": top_result['label'],
                        "score": top_result['score']
                    })
                else:
                    emotion_results.append({"label": "neutral", "score": 0.0})

            return emotion_results

        except Exception as e:
            logger.error(f"❌ Error in emotion batch analysis: {e}")
            return [{"label": "neutral", "score": 0.0} for _ in texts]

