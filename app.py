import gradio as gr
import librosa
import numpy as np
from scipy import signal
import mido
from mido import MidiFile, MidiTrack, Message
import tempfile
import os


def mp3_to_midi(audio_file, threshold=0.1, hop_length=512):
    """
    Convert MP3 audio to MIDI file.
    
    Args:
        audio_file: Path to MP3 file
        threshold: Confidence threshold for note detection (0-1)
        hop_length: Number of samples between successive frames
    
    Returns:
        Path to generated MIDI file
    """
    try:
        # Load audio file
        y, sr = librosa.load(audio_file, sr=None)
        
        # Compute constant-Q transform for pitch detection
        fmin = librosa.note_to_hz('C1')
        n_bins = 84
        bins_per_octave = 12
        
        cqt = librosa.cqt(y, sr=sr, hop_length=hop_length, fmin=fmin, n_bins=n_bins, bins_per_octave=bins_per_octave)
        cqt_magnitude = np.abs(cqt)
        
        # Get the note with maximum magnitude at each time step
        notes = np.argmax(cqt_magnitude, axis=0)
        
        # Compute frequencies for each CQT bin
        frequencies = librosa.cqt_frequencies(n_bins=n_bins, fmin=fmin, bins_per_octave=bins_per_octave)
        
        # Get magnitude values
        note_magnitudes = cqt_magnitude[notes, np.arange(len(notes))]
        
        # Normalize magnitudes
        max_magnitude = np.max(note_magnitudes)
        normalized_magnitudes = note_magnitudes / max_magnitude if max_magnitude > 0 else note_magnitudes
        
        # Apply threshold
        active_notes = normalized_magnitudes > threshold
        
        # Create MIDI file
        mid = MidiFile()
        track = MidiTrack()
        mid.tracks.append(track)
        
        # Set tempo (microseconds per beat)
        tempo = mido.bpm2tempo(120)
        track.append(Message('program_change', program=0, time=0))
        
        # Calculate time per frame in ticks
        time_per_frame = int((60 * 1000000 / tempo) / (sr / hop_length) * 1000)
        
        current_note = None
        note_start = 0
        
        for i in range(len(notes)):
            freq = frequencies[notes[i]]
            
            # Convert frequency to MIDI note number
            midi_note = librosa.hz_to_midi(freq)
            midi_note = int(round(midi_note))
            
            # Clamp to valid MIDI range
            midi_note = max(0, min(127, midi_note))
            
            if active_notes[i]:
                if current_note is None or current_note != midi_note:
                    # Note changed or new note started
                    if current_note is not None:
                        # End previous note
                        duration = max(1, (i - note_start) * time_per_frame)
                        track.append(Message('note_off', note=current_note, velocity=80, time=duration))
                    
                    # Start new note
                    track.append(Message('note_on', note=midi_note, velocity=100, time=0))
                    current_note = midi_note
                    note_start = i
            else:
                if current_note is not None:
                    # End current note
                    duration = max(1, (i - note_start) * time_per_frame)
                    track.append(Message('note_off', note=current_note, velocity=80, time=duration))
                    current_note = None
        
        # End any remaining note
        if current_note is not None:
            duration = max(1, (len(notes) - note_start) * time_per_frame)
            track.append(Message('note_off', note=current_note, velocity=80, time=duration))
        
        # Save MIDI file
        output_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mid')
        output_path = output_file.name
        output_file.close()
        
        mid.save(output_path)
        
        return output_path, "✓ Conversion successful!"
    
    except Exception as e:
        return None, f"✗ Error: {str(e)}"


def create_interface():
    """Create and launch the Gradio interface"""
    
    with gr.Blocks(title="MP3 to MIDI Converter") as demo:
        gr.Markdown(
            """
            # 🎵 MP3 to MIDI Converter
            
            Convert your MP3 audio files to MIDI format using pitch detection.
            
            **How it works:**
            1. Upload an MP3 file
            2. Adjust the sensitivity threshold (lower = more notes detected)
            3. Click Convert
            4. Download the generated MIDI file
            """
        )
        
        with gr.Row():
            with gr.Column():
                gr.Markdown("### Input")
                audio_input = gr.Audio(
                    label="Upload MP3 File",
                    type="filepath"
                )
                
                threshold = gr.Slider(
                    minimum=0.01,
                    maximum=0.5,
                    value=0.1,
                    step=0.01,
                    label="Detection Threshold",
                    info="Lower values detect quieter notes (more sensitive)"
                )
                
                convert_btn = gr.Button("🎹 Convert to MIDI", variant="primary", scale=2)
            
            with gr.Column():
                gr.Markdown("### Output")
                status_text = gr.Textbox(
                    label="Status",
                    interactive=False,
                    lines=1
                )
                
                midi_output = gr.File(
                    label="Download MIDI File",
                    interactive=False
                )
        
        gr.Markdown(
            """
            ### Tips for Best Results
            - **Clear audio**: Use high-quality recordings for better pitch detection
            - **Single instrument**: Works best with monophonic (single-note) audio
            - **Adjust sensitivity**: If you're getting too many notes, increase threshold
            - **Clean recordings**: Minimize background noise for accurate conversion
            """
        )
        
        # Handle conversion
        def convert(audio_file, threshold_val):
            if audio_file is None:
                return None, "✗ Please upload an MP3 file"
            
            midi_path, status = mp3_to_midi(audio_file, threshold=threshold_val)
            
            if midi_path and os.path.exists(midi_path):
                return midi_path, status
            else:
                return None, status
        
        convert_btn.click(
            fn=convert,
            inputs=[audio_input, threshold],
            outputs=[midi_output, status_text]
        )
    
    return demo


if __name__ == "__main__":
    demo = create_interface()
    demo.launch(share=False)
