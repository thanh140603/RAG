"""
Chunker - Infrastructure Layer
Single Responsibility: Split text into chunks
Open/Closed: Can be extended with different chunking strategies
"""
from __future__ import annotations

import re
from typing import List, Optional
from uuid import uuid4

from src.domain.entities.Chunk import Chunk
from src.config.settings import get_settings

settings = get_settings()


class Chunker:
    """
    Text chunker with semantic chunking support
    Single Responsibility: Split documents into chunks
    """

    def __init__(
        self,
        chunk_size: int | None = None,
        chunk_overlap: int | None = None,
        use_semantic: bool = True,
        embedder=None,  # Optional embedder for semantic chunking
    ):
        self.chunk_size = chunk_size or settings.chunk_size
        self.chunk_overlap = chunk_overlap or settings.chunk_overlap
        self.use_semantic = use_semantic
        self._embedder = embedder

    async def chunk(self, text: str, document_id: str) -> List[Chunk]:
        """
        Split text into chunks using semantic chunking if enabled, otherwise fixed-size
        """
        if not text:
            return []

        if self.use_semantic and self._embedder:
            return await self._semantic_chunk(text, document_id)
        else:
            return await self._fixed_size_chunk(text, document_id)

    async def _fixed_size_chunk(self, text: str, document_id: str) -> List[Chunk]:
        """
        Split text into overlapping fixed-size chunks (original method)
        """
        chunks: List[Chunk] = []
        length = len(text)
        start = 0
        order = 0
        overlap = min(self.chunk_overlap, self.chunk_size // 2)

        while start < length:
            end = min(length, start + self.chunk_size)
            chunk_text = text[start:end].strip()
            if chunk_text:
                chunks.append(
                    Chunk(
                        id=str(uuid4()),
                        document_id=document_id,
                        order=order,
                        text=chunk_text,
                        start_offset=start,
                        end_offset=end,
                        metadata={"order": order, "source": "fixed_size_chunker"},
                    )
                )
                order += 1
            if end >= length:
                break
            start = max(0, end - overlap)

        return chunks

    async def _semantic_chunk(self, text: str, document_id: str) -> List[Chunk]:
        """
        Split text into semantic chunks based on similarity between sentences/paragraphs
        
        Algorithm:
        1. Split text into sentences/paragraphs
        2. Create small segments (sentences grouped)
        3. Calculate embeddings for each segment
        4. Find semantic boundaries (low similarity between consecutive segments)
        5. Group segments into chunks respecting min/max size constraints
        """
        # Step 1: Split into sentences
        sentences = self._split_into_sentences(text)
        if len(sentences) < 2:
            # Fallback to fixed-size if too few sentences
            return await self._fixed_size_chunk(text, document_id)

        # Step 2: Group sentences into segments (smaller units for comparison)
        segment_size = max(2, self.chunk_size // 500)  # ~2-3 sentences per segment
        segments = []
        segment_texts = []
        
        # Calculate actual offsets in original text
        current_pos = 0
        for i in range(0, len(sentences), segment_size):
            segment_sentences = sentences[i:i + segment_size]
            segment_text = " ".join(segment_sentences)
            
            # Find actual position in original text
            segment_start = text.find(segment_sentences[0], current_pos)
            if segment_start == -1:
                segment_start = current_pos
            segment_end = segment_start + len(segment_text)
            current_pos = segment_end
            
            segments.append({
                "start": segment_start,
                "end": segment_end,
                "text": segment_text,
                "sentences": segment_sentences
            })
            segment_texts.append(segment_text)

        if len(segments) < 2:
            return await self._fixed_size_chunk(text, document_id)

        # Step 3: Calculate embeddings for segments
        embeddings = await self._embedder.embed_batch(segment_texts)

        # Step 4: Find semantic boundaries (low similarity = good split point)
        boundaries = self._find_semantic_boundaries(embeddings, threshold=0.7)

        # Step 5: Group segments into chunks
        chunks = self._group_into_chunks(
            segments, boundaries, text, document_id
        )

        return chunks

    def _split_into_sentences(self, text: str) -> List[str]:
        """
        Split text into sentences using regex
        """
        # Pattern to match sentence endings (. ! ?) followed by space or end
        sentence_pattern = r'(?<=[.!?])\s+(?=[A-Z])|(?<=[.!?])\s*$'
        sentences = re.split(sentence_pattern, text)
        # Filter out empty sentences
        sentences = [s.strip() for s in sentences if s.strip()]
        return sentences

    def _find_semantic_boundaries(
        self, 
        embeddings: List[List[float]], 
        threshold: float = 0.7
    ) -> List[int]:
        """
        Find semantic boundaries by comparing consecutive embeddings
        Returns list of indices where semantic breaks occur (good split points)
        """
        boundaries = [0]  # Always start at beginning
        
        for i in range(len(embeddings) - 1):
            similarity = self._cosine_similarity(
                embeddings[i], 
                embeddings[i + 1]
            )
            # Low similarity = semantic boundary
            if similarity < threshold:
                boundaries.append(i + 1)
        
        return boundaries

    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """
        Calculate cosine similarity between two vectors
        """
        if len(vec1) != len(vec2):
            return 0.0
        
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        magnitude1 = sum(a * a for a in vec1) ** 0.5
        magnitude2 = sum(b * b for b in vec2) ** 0.5
        
        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0
        
        return dot_product / (magnitude1 * magnitude2)

    def _group_into_chunks(
        self,
        segments: List[dict],
        boundaries: List[int],
        full_text: str,
        document_id: str
    ) -> List[Chunk]:
        """
        Group segments into chunks respecting size constraints
        """
        chunks: List[Chunk] = []
        min_chunk_size = self.chunk_size // 2  # Minimum chunk size
        max_chunk_size = self.chunk_size * 2   # Maximum chunk size
        
        order = 0
        current_chunk_segments = []
        current_chunk_start = 0
        
        for i, segment in enumerate(segments):
            # Check if we should start a new chunk
            should_split = (
                i in boundaries or  # Semantic boundary
                (current_chunk_segments and 
                 sum(len(s["text"]) for s in current_chunk_segments) + len(segment["text"]) > max_chunk_size)
            )
            
            if should_split and current_chunk_segments:
                # Create chunk from accumulated segments
                chunk_text = " ".join(s["text"] for s in current_chunk_segments)
                if len(chunk_text) >= min_chunk_size:
                    start_offset = current_chunk_segments[0]["start"]
                    end_offset = current_chunk_segments[-1]["end"]
                    
                    chunks.append(
                        Chunk(
                            id=str(uuid4()),
                            document_id=document_id,
                            order=order,
                            text=chunk_text.strip(),
                            start_offset=start_offset,
                            end_offset=end_offset,
                            metadata={
                                "order": order,
                                "source": "semantic_chunker",
                                "segment_count": len(current_chunk_segments)
                            },
                        )
                    )
                    order += 1
                
                # Start new chunk with overlap
                if current_chunk_segments:
                    # Keep last segment for overlap
                    overlap_segments = current_chunk_segments[-1:]
                    current_chunk_segments = overlap_segments + [segment]
                    current_chunk_start = overlap_segments[0]["start"]
                else:
                    current_chunk_segments = [segment]
                    current_chunk_start = segment["start"]
            else:
                current_chunk_segments.append(segment)
        
        # Add final chunk
        if current_chunk_segments:
            chunk_text = " ".join(s["text"] for s in current_chunk_segments)
            if len(chunk_text) >= min_chunk_size:
                start_offset = current_chunk_segments[0]["start"]
                end_offset = current_chunk_segments[-1]["end"]
                
                chunks.append(
                    Chunk(
                        id=str(uuid4()),
                        document_id=document_id,
                        order=order,
                        text=chunk_text.strip(),
                        start_offset=start_offset,
                        end_offset=end_offset,
                        metadata={
                            "order": order,
                            "source": "semantic_chunker",
                            "segment_count": len(current_chunk_segments)
                        },
                    )
                )
        
        return chunks

