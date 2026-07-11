import client from './client'

export const startGame = playerNames => client.post('/start_game', { player_names: playerNames })
export const playCards = cardIndices => client.post('/play', { card_indices: cardIndices })
export const passTurn = () => client.post('/pass')
export const getRecommendation = strategy => client.post('/recommend', { strategy })
export const getHistory = () => client.get('/history')
