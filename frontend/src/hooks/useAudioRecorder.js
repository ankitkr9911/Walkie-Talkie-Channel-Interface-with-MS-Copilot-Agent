/**
 * useAudioRecorder — Custom hook for Hold-To-Talk recording
 * ==========================================================
 * Uses the MediaRecorder API to capture audio from the laptop microphone.
 * Records while the user holds down the PTT button, stops on release.
 * Returns a Blob (webm/opus format) ready to upload to the backend.
 */

import { useState, useRef, useCallback } from 'react';

export default function useAudioRecorder() {
  const [isRecording, setIsRecording] = useState(false);
  const mediaRecorder = useRef(null);
  const audioChunks = useRef([]);

  /** Start recording — called on mousedown/touchstart of PTT button */
  const startRecording = useCallback(async () => {
    try {
      // Request microphone access
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });

      // Create recorder with webm format (widely supported)
      const recorder = new MediaRecorder(stream, {
        mimeType: MediaRecorder.isTypeSupported('audio/webm;codecs=opus')
          ? 'audio/webm;codecs=opus'
          : 'audio/webm',
      });

      audioChunks.current = [];

      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) audioChunks.current.push(e.data);
      };

      mediaRecorder.current = recorder;
      recorder.start(100); // Collect data every 100ms
      setIsRecording(true);
    } catch (err) {
      console.error('Microphone access denied:', err);
      alert('Please allow microphone access to use Hold-To-Talk.');
    }
  }, []);

  /** Stop recording — called on mouseup/touchend. Returns audio Blob. */
  const stopRecording = useCallback(() => {
    return new Promise((resolve) => {
      const recorder = mediaRecorder.current;
      if (!recorder || recorder.state === 'inactive') {
        resolve(null);
        return;
      }

      recorder.onstop = () => {
        // Combine chunks into a single Blob
        const blob = new Blob(audioChunks.current, { type: 'audio/webm' });

        // Stop all tracks to release the microphone
        recorder.stream.getTracks().forEach((track) => track.stop());

        setIsRecording(false);
        resolve(blob);
      };

      recorder.stop();
    });
  }, []);

  return { isRecording, startRecording, stopRecording };
}
