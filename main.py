/** @jsxImportSource https://esm.sh/react@18.2.0 */
import React, { useState, useEffect } from "https://esm.sh/react@18.2.0";
import { createRoot } from "https://esm.sh/react-dom@18.2.0/client";

// Utility function for web scraping
async function scrapeWebsite(options) {
  const { 
    url, 
    selector = 'a', 
    maxPages = 100, 
    filterRegex = null,
    useProxy = false
  } = options;

  const { sqlite } = await import("https://esm.town/v/stevekrouse/sqlite");
  const KEY = new URL(import.meta.url).pathname.split("/").at(-1);

  // Create scrape results table
  await sqlite.execute(`
    CREATE TABLE IF NOT EXISTS ${KEY}_scrape_results (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      url TEXT,
      source_page TEXT,
      timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
  `);

  // Proxy list (in a real-world scenario, use a paid proxy service)
  const proxies = [
    'https://proxy1.example.com',
    'https://proxy2.example.com',
    'https://proxy3.example.com'
  ];

  const results = [];
  const errors = [];

  for (let page = 1; page <= maxPages; page++) {
    try {
      // Simulate rate limiting and proxy rotation
      await new Promise(resolve => setTimeout(resolve, 1000)); // 1 second between requests

      const pageUrl = `${url}?page=${page}`;
      
      // Proxy rotation logic
      const proxyUrl = useProxy 
        ? proxies[Math.floor(Math.random() * proxies.length)] 
        : null;

      const response = await fetch(proxyUrl ? `${proxyUrl}/${pageUrl}` : pageUrl, {
        headers: {
          'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
          'Accept-Language': 'en-US,en;q=0.9'
        }
      });

      if (!response.ok) {
        errors.push(`Failed to fetch ${pageUrl}: ${response.status}`);
        break;
      }

      const html = await response.text();
      
      // Use a more robust parsing method
      const links = html.match(/<a[^>]+href=["']([^"']+)["'][^>]*>/gi) || [];

      const pageResults = links
        .map(link => {
          const match = link.match(/href=["']([^"']+)["']/i);
          return match ? match[1] : null;
        })
        .filter(url => 
          url && 
          (filterRegex ? filterRegex.test(url) : true) &&
          (url.startsWith('http') || url.startsWith('/'))
        );

      // Store results in SQLite
      for (const link of pageResults) {
        await sqlite.execute(`
          INSERT INTO ${KEY}_scrape_results (url, source_page) 
          VALUES (?, ?)
        `, [link, pageUrl]);
        
        results.push(link);
      }

      // Stop if no more results
      if (pageResults.length === 0) break;

    } catch (error) {
      errors.push(`Error on page ${page}: ${error.message}`);
      break;
    }
  }

  return {
    results,
    errors,
    totalResults: results.length
  };
}

function WebScraperInterface() {
  const [scrapeOptions, setScrapeOptions] = useState({
    url: '',
    selector: 'a',
    maxPages: 100,
    filterRegex: '',
    useProxy: false
  });

  const [scrapeResults, setScrapeResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // New function to generate and download files
  const downloadFile = (format) => {
    if (!scrapeResults) return;

    let content, filename, mimetype;
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');

    switch(format) {
      case 'csv':
        content = scrapeResults.results.map(url => `"${url}"`).join('\n');
        filename = `scrape_results_${timestamp}.csv`;
        mimetype = 'text/csv';
        break;
      case 'json':
        content = JSON.stringify(scrapeResults.results, null, 2);
        filename = `scrape_results_${timestamp}.json`;
        mimetype = 'application/json';
        break;
      case 'txt':
      default:
        content = scrapeResults.results.join('\n');
        filename = `scrape_results_${timestamp}.txt`;
        mimetype = 'text/plain';
    }

    const blob = new Blob([content], { type: mimetype });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setScrapeResults(null);
    setError(null);

    try {
      const regex = scrapeOptions.filterRegex 
        ? new RegExp(scrapeOptions.filterRegex) 
        : null;

      const results = await fetch('/scrape', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ...scrapeOptions,
          filterRegex: regex ? regex.source : null
        })
      }).then(res => res.json());

      setScrapeResults(results);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ 
      maxWidth: '800px', 
      margin: 'auto', 
      padding: '20px', 
      fontFamily: 'Arial, sans-serif' 
    }}>
      <h1>🕸️ Advanced Web Scraper</h1>
      <form onSubmit={handleSubmit}>
        <div style={{ marginBottom: '15px' }}>
          <label>Target URL:</label>
          <input 
            type="url" 
            value={scrapeOptions.url}
            onChange={(e) => setScrapeOptions({...scrapeOptions, url: e.target.value})}
            placeholder="https://example.com"
            required 
            style={{ width: '100%', padding: '10px' }}
          />
        </div>

        <div style={{ display: 'flex', gap: '15px' }}>
          <div style={{ flex: 1 }}>
            <label>Max Pages:</label>
            <input 
              type="number" 
              value={scrapeOptions.maxPages}
              onChange={(e) => setScrapeOptions({...scrapeOptions, maxPages: parseInt(e.target.value)})}
              min="1" 
              max="1000"
              style={{ width: '100%', padding: '10px' }}
            />
          </div>
          <div style={{ flex: 1 }}>
            <label>CSS Selector:</label>
            <input 
              type="text" 
              value={scrapeOptions.selector}
              onChange={(e) => setScrapeOptions({...scrapeOptions, selector: e.target.value})}
              placeholder="a"
              style={{ width: '100%', padding: '10px' }}
            />
          </div>
        </div>

        <div style={{ marginBottom: '15px' }}>
          <label>Filter Regex (optional):</label>
          <input 
            type="text" 
            value={scrapeOptions.filterRegex}
            onChange={(e) => setScrapeOptions({...scrapeOptions, filterRegex: e.target.value})}
            placeholder=".*youtube\.com.*"
            style={{ width: '100%', padding: '10px' }}
          />
        </div>

        <div style={{ marginBottom: '15px' }}>
          <label>
            <input 
              type="checkbox" 
              checked={scrapeOptions.useProxy}
              onChange={(e) => setScrapeOptions({...scrapeOptions, useProxy: e.target.checked})}
            />
            Use Proxy (Experimental)
          </label>
        </div>

        <button 
          type="submit" 
          disabled={loading}
          style={{ 
            width: '100%', 
            padding: '10px', 
            backgroundColor: loading ? '#ccc' : '#4CAF50',
            color: 'white',
            border: 'none'
          }}
        >
          {loading ? 'Scraping...' : 'Start Web Scraping'}
        </button>
      </form>

      {error && (
        <div style={{ 
          color: 'red', 
          marginTop: '15px', 
          padding: '10px', 
          backgroundColor: '#ffeeee' 
        }}>
          Error: {error}
        </div>
      )}

      {scrapeResults && (
        <div style={{ marginTop: '20px' }}>
          <h2>Scrape Results</h2>
          <p>Total Links Found: {scrapeResults.totalResults}</p>
          {scrapeResults.errors.length > 0 && (
            <div style={{ color: 'orange' }}>
              <h3>Warnings:</h3>
              {scrapeResults.errors.map((err, i) => (
                <p key={i}>{err}</p>
              ))}
            </div>
          )}
          <div style={{ 
            maxHeight: '300px', 
            overflowY: 'auto', 
            border: '1px solid #ddd', 
            padding: '10px' 
          }}>
            {scrapeResults.results.slice(0, 100).map((url, i) => (
              <div key={i}>{url}</div>
            ))}
            {scrapeResults.results.length > 100 && (
              <p>... and {scrapeResults.results.length - 100} more</p>
            )}
          </div>

          {/* New Download Buttons */}
          <div style={{ 
            display: 'flex', 
            justifyContent: 'space-between', 
            marginTop: '15px' 
          }}>
            <button 
              onClick={() => downloadFile('csv')}
              style={{ 
                padding: '10px', 
                backgroundColor: '#2196F3', 
                color: 'white', 
                border: 'none' 
              }}
            >
              Download CSV
            </button>
            <button 
              onClick={() => downloadFile('json')}
              style={{ 
                padding: '10px', 
                backgroundColor: '#4CAF50', 
                color: 'white', 
                border: 'none' 
              }}
            >
              Download JSON
            </button>
            <button 
              onClick={() => downloadFile('txt')}
              style={{ 
                padding: '10px', 
                backgroundColor: '#FF9800', 
                color: 'white', 
                border: 'none' 
              }}
            >
              Download TXT
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

function App() {
  return (
    <div>
      <WebScraperInterface />
      <a 
        href={import.meta.url.replace("esm.town", "val.town")} 
        target="_top" 
        style={{ 
          display: 'block', 
          textAlign: 'center', 
          marginTop: '20px', 
          color: '#666', 
          textDecoration: 'none' 
        }}
      >
        View Web Scraper Source
      </a>
    </div>
  );
}

function client() {
  createRoot(document.getElementById("root")).render(<App />);
}
if (typeof document !== "undefined") { client(); }

export default async function server(request: Request): Promise<Response> {
  // Handle scraping request
  if (request.method === 'POST' && new URL(request.url).pathname === '/scrape') {
    try {
      const options = await request.json();
      const scrapeResults = await scrapeWebsite({
        ...options,
        filterRegex: options.filterRegex ? new RegExp(options.filterRegex) : null
      });

      return new Response(JSON.stringify(scrapeResults), {
        headers: { 'Content-Type': 'application/json' }
      });
    } catch (error) {
      return new Response(JSON.stringify({ 
        error: error.message,
        results: [],
        errors: [error.message]
      }), { 
        status: 500,
        headers: { 'Content-Type': 'application/json' }
      });
    }
  }

  // Render main page
  return new Response(`
    <html>
      <head>
        <title>Advanced Web Scraper</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
      </head>
      <body>
        <div id="root"></div>
        <script src="https://esm.town/v/std/catch"></script>
        <script type="module" src="${import.meta.url}"></script>
      </body>
    </html>
  `, {
    headers: { "content-type": "text/html" }
  });
}
