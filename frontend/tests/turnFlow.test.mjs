import assert from 'node:assert/strict'
import test from 'node:test'

import { catchWindPlayerIndex, nextActivePlayerIndex, recordFinish, requiredPasses } from '../store/turnFlow.mjs'

const players = counts => counts.map((hand_count, index) => ({ name: `玩家${index + 1}`, hand_count }))

test('正常轮转按座位顺序进行', () => {
  assert.equal(nextActivePlayerIndex(players([5, 5, 5, 5]), 0), 1)
})

test('轮转会跳过已经出完牌的玩家', () => {
  assert.equal(nextActivePlayerIndex(players([5, 0, 5, 5]), 0), 2)
})

test('玩家出完后优先由对家接风', () => {
  assert.equal(catchWindPlayerIndex(players([0, 5, 5, 5]), 0), 2)
})

test('对家已经出完时由下一名活跃玩家接风', () => {
  assert.equal(catchWindPlayerIndex(players([0, 5, 0, 5]), 0), 1)
})

test('PASS阈值随仍有手牌的玩家数量变化', () => {
  assert.equal(requiredPasses(players([5, 5, 5, 5])), 3)
  assert.equal(requiredPasses(players([5, 0, 5, 5])), 2)
  assert.equal(requiredPasses(players([5, 0, 5, 0])), 1)
})

test('三人出完后补齐末游并结束牌局', () => {
  const game = { phase: 'playing', winner: null, players: players([0, 0, 0, 3]), state: { finish_order: ['玩家1', '玩家2'] } }
  assert.equal(recordFinish(game, 2), null)
  assert.equal(game.phase, 'finished')
  assert.deepEqual(game.state.finish_order, ['玩家1', '玩家2', '玩家3', '玩家4'])
})
