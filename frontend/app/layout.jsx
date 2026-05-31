import '../styles/globals.css';

export const metadata = {
  title: 'Kulima OS - Community Demand Insights',
  description: 'Turn local activity into community-ready planning intelligence for energy and infrastructure decisions.',
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
