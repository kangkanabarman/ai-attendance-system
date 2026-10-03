from resemblyzer import VoiceEncoder, preprocess_wav
import numpy as np
import io
import librosa
import streamlit as st

@st.cache_resource
def load_voice_encoder():
    return VoiceEncoder()

def get_voice_embedding(audio_bytes):
    try:
        encoder = load_voice_encoder()
        audio, sr = librosa.load(io.BytesIO(audio_bytes), sr=16000)
        wav = preprocess_wav(audio)
        embedding = encoder.embed_utterance(wav)
        return embedding.tolist()
    except Exception as e:
        import traceback
        st.error(f"Voice error: {e}")
        traceback.print_exc()
        return None

def cosine_similarity(a, b):
    a_norm = np.linalg.norm(a)
    b_norm = np.linalg.norm(b)
    if a_norm == 0 or b_norm == 0:
        return 0.0
    return float(np.dot(a, b) / (a_norm * b_norm))

def identify_speaker(new_embedding, candidates_dict, threshold=0.65):
    """
    Matches new voice embedding against candidate dictionary {student_id: stored_embedding}.
    Returns (best_student_id, best_score) if score >= threshold, else (None, best_score).
    """
    if new_embedding is None or not candidates_dict:
        return None, 0.0

    best_sid = None
    best_score = -1.0

    new_emb_np = np.array(new_embedding)

    for sid, stored_embedding in candidates_dict.items():
        if stored_embedding:
            stored_emb_np = np.array(stored_embedding)
            similarity = cosine_similarity(new_emb_np, stored_emb_np)
            if similarity > best_score:
                best_score = similarity
                best_sid = sid

    if best_score >= threshold and best_sid is not None:
        return best_sid, best_score
    return None, best_score

def process_bulk_audio(audio_bytes, candidates_dict, threshold=0.65):
    """
    Processes a multi-utterance audio recording by segmenting speech and identifying speakers.
    Returns a dictionary of {student_id: confidence_score}.
    """
    try:
        encoder = load_voice_encoder()
        audio, sr = librosa.load(io.BytesIO(audio_bytes), sr=16000)
        segments = librosa.effects.split(audio, top_db=30)

        identified_results = {}

        for start, end in segments:
            if (end - start) < sr * 0.5:
                continue
            segment_audio = audio[start:end]
            wav = preprocess_wav(segment_audio)
            embedding = encoder.embed_utterance(wav)

            sid, score = identify_speaker(embedding, candidates_dict, threshold)
            if sid is not None:
                if sid not in identified_results or score >= identified_results[sid]:
                    identified_results[sid] = round(score, 3)

        return identified_results
    except Exception as e:
        st.error(f"Bulk voice process error: {e}")
        return {}
