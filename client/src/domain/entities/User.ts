export interface User {
  id: string
  email: string
  name: string
  role: 'admin' | 'user'
  created_at: string
  updated_at: string
}

