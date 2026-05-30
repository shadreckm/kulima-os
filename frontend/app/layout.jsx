import '../styles/globals.css';

export const metadata = {
  title: 'Kulima OS - Coordination Intelligence Platform',
  description: 'Transform real-world activity into decision-grade intelligence for infrastructure planning',
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <head>
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <link rel="icon" href="/favicon.ico" />
      </head>
      <body>
        {children}
      </body>
    </html>
  );
}
