import ChatWidget from './components/ChatWidget';

/**
 * App — Root component
 * ChatWidget is full-page (flex row: sidebar + main panel).
 * No wrapper div needed — ChatWidget manages the full viewport.
 */
export default function App() {
  return <ChatWidget />;
}
