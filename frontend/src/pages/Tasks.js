import Layout from '@/components/Layout';
export default function Tasks({ user, onLogout }) {
  return <Layout user={user} onLogout={onLogout}><div className="text-2xl font-bold">Tasks - Coming Soon</div></Layout>;
}
