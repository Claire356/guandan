// 离线牌局的座位轮转工具。这里只管理顺序，不参与牌型和大小判断。
export const isActivePlayer = player => Number(player?.hand_count || 0) > 0

export const nextActivePlayerIndex = (players, startIndex) => {
  for (let offset = 1; offset <= players.length; offset += 1) {
    const candidate = (startIndex + offset) % players.length
    if (isActivePlayer(players[candidate])) return candidate
  }
  return startIndex
}

// 接风优先交给对家；对家已经出完时，按座位顺序交给下一名仍有牌的玩家。
export const catchWindPlayerIndex = (players, finishedIndex) => {
  const partnerIndex = (finishedIndex + 2) % players.length
  if (isActivePlayer(players[partnerIndex])) return partnerIndex
  return nextActivePlayerIndex(players, finishedIndex)
}

// 四人均在场时需要三家 PASS；有人出完后只等待仍在牌局中的其他玩家。
export const requiredPasses = players => Math.max(1, players.filter(isActivePlayer).length - 1)

export const recordFinish = (game, finishedIndex) => {
  const state = game.state
  const name = game.players[finishedIndex].name
  state.finish_order = state.finish_order || []
  if (!state.finish_order.includes(name)) state.finish_order.push(name)
  if (!game.winner) game.winner = name

  // 三人出完时名次已经完整确定，最后一人直接记为末游并结束牌局。
  if (state.finish_order.length === game.players.length - 1) {
    const last = game.players.find(player => !state.finish_order.includes(player.name))
    if (last) state.finish_order.push(last.name)
    game.phase = 'finished'
    state.phase = 'finished'
    return null
  }
  return catchWindPlayerIndex(game.players, finishedIndex)
}
