import { http } from './http'

export async function initDb() {
  const { data } = await http.post('/db/init')
  return data
}
