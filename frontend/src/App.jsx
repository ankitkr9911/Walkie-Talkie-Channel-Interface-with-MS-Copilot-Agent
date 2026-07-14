import ChatWidget from './components/ChatWidget';

/**
 * App — Root component
 * The entire app is a single ChatWidget card matching the design reference.
 * No routing needed — this is a single-page voice/chat interface.
 */
export default function App() {
  return (
    <div className="app-container">
      <ChatWidget />
    </div>
  );
}
