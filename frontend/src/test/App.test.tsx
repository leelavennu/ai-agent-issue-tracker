import { render, screen, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import App from '../App';

test('shows empty state when API returns no issues', async () => {
  globalThis.fetch = jest.fn().mockResolvedValue({ok:true,json:async()=>({items:[],total:0,page:1,limit:10,pages:0})}) as jest.Mock;
  render(<BrowserRouter><App /></BrowserRouter>);
  expect(await screen.findByText('No issues found')).toBeInTheDocument();
});

test('shows failed API state', async () => {
  globalThis.fetch = jest.fn().mockRejectedValue(new Error('network')) as jest.Mock;
  render(<BrowserRouter><App /></BrowserRouter>);
  await waitFor(()=>expect(screen.getByText(/Failed to load/)).toBeInTheDocument());
});
