import { cp, mkdir } from 'node:fs/promises'
import { resolve } from 'node:path'

const source = resolve('static')
const target = resolve('dist/build/h5')

await mkdir(target, { recursive: true })
await cp(source, target, { recursive: true, force: true })
console.info('PWA 静态资源已复制到 dist/build/h5')
