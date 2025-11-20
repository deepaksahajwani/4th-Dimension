import { useSearchParams } from 'react-router-dom';
import { useEffect, useState } from 'react';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function EmailPreview() {
  const [searchParams] = useSearchParams();
  const [emailContent, setEmailContent] = useState('');
  const [loading, setLoading] = useState(true);
  
  const userId = searchParams.get('user');
  const role = searchParams.get('role');
  const lang = searchParams.get('lang') || 'en';

  useEffect(() => {
    const fetchEmailContent = async () => {
      try {
        const response = await axios.get(`${API}/email-preview`, {
          params: { user_id: userId, role: role, lang: lang }
        });
        setEmailContent(response.data.html_content);
      } catch (error) {
        console.error('Error fetching email:', error);
        setEmailContent('<div style="padding: 40px; text-align: center;"><h2>Error loading email preview</h2></div>');
      } finally {
        setLoading(false);
      }
    };

    fetchEmailContent();
  }, [userId, role, lang]);

  if (loading) {
    return (
      <div style={{ 
        display: 'flex', 
        justifyContent: 'center', 
        alignItems: 'center', 
        minHeight: '100vh',
        fontFamily: 'Arial, sans-serif' 
      }}>
        <div>Loading email preview...</div>
      </div>
    );
  }

  return (
    <div 
      dangerouslySetInnerHTML={{ __html: emailContent }}
      style={{ 
        minHeight: '100vh',
        backgroundColor: '#F9FAFB',
        padding: '20px'
      }}
    />
  );
}
