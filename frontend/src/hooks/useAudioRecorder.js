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
  const streamRef = useRef(null);   // Track the raw stream so we can always release it
  const audioChunks = useRef([]);

  /** Clean up any leftover stream/recorder from a previous (possibly failed) session */
  const _cleanup = useCallback(() => {
    if (mediaRecorder.current && mediaRecorder.current.state !== 'inactive') {
      try { mediaRecorder.current.stop(); } catch (_) {}
    }
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((t) => { try { t.stop(); } catch (_) {} });
      streamRef.current = null;
    }
    mediaRecorder.current = null;
    audioChunks.current = [];
    setIsRecording(false);
  }, []);

  /** Start recording — called on mousedown/touchstart of PTT button */
  const startRecording = useCallback(async () => {
    // Always clean up stale state first — prevents button getting stuck after errors
    _cleanup();

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;

      // Use webm/opus if supported, fall back to plain webm
      const mimeType = MediaRecorder.isTypeSupported('audio/webm;codecs=opus')
        ? 'audio/webm;codecs=opus'
        : 'audio/webm';

      const recorder = new MediaRecorder(stream, { mimeType });
      audioChunks.current = [];

      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) audioChunks.current.push(e.data);
      };

      mediaRecorder.current = recorder;
      recorder.start(100); // Collect audio every 100ms
      setIsRecording(true);
    } catch (err) {
      console.error('Microphone access error:', err);
      setIsRecording(false);
      // Show alert only for actual permission denials, not other errors
      if (err.name === 'NotAllowedError' || err.name === 'PermissionDeniedError') {
        alert('Microphone access was denied. Click the 🎤 icon in your browser address bar to allow it, then try again.');
      }
    }
  }, [_cleanup]);

  /** Stop recording — called on mouseup/touchend. Returns audio Blob. */
  const stopRecording = useCallback(() => {
    return new Promise((resolve) => {
      const recorder = mediaRecorder.current;

      if (!recorder || recorder.state === 'inactive') {
        setIsRecording(false);
        resolve(null);
        return;
      }

      recorder.onstop = () => {
        const blob = new Blob(audioChunks.current, { type: 'audio/webm' });

        // Release the microphone
        if (streamRef.current) {
          streamRef.current.getTracks().forEach((t) => { try { t.stop(); } catch (_) {} });
          streamRef.current = null;
        }

        setIsRecording(false);
        resolve(blob);
      };

      recorder.stop();
    });
  }, []);

  return { isRecording, startRecording, stopRecording };
}
