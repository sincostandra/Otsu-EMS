import api from './client'

// Downloads through axios so the JWT header is sent, then triggers a save.
export async function downloadExport(resource, format, params = {}) {
  const response = await api.get(`/${resource}/export/`, {
    params: { ...params, format },
    responseType: 'blob',
  })
  const url = URL.createObjectURL(response.data)
  const link = document.createElement('a')
  link.href = url
  link.download = `${resource}.${format}`
  document.body.appendChild(link)
  link.click()
  link.remove()
  URL.revokeObjectURL(url)
}
