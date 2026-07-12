<template>
  <view class="table-page safe-bottom">
    <view class="table-head">
      <u-icon name="arrow-left" color="#fff" size="24" @click="back" />
      <text>第 {{ store.game?.round_number || 1 }} 局</text>
      <u-tag :text="store.offlineDemo ? '离线演示' : '在线训练'" size="mini" bgColor="rgba(255,255,255,.16)" borderColor="transparent" color="#fff" />
    </view>

    <view class="game-table">
      <view class="player top"><view class="avatar">AI</view><text>AI-2</text><text class="count">{{ playerCount('AI-2') }}张</text></view>
      <view class="player left"><view class="avatar">AI</view><text>AI-1</text><text class="count">{{ playerCount('AI-1') }}张</text></view>
      <view class="player right"><view class="avatar">AI</view><text>AI-3</text><text class="count">{{ playerCount('AI-3') }}张</text></view>
      <view v-for="name in playerNames" :key="name" class="table-play" :class="playPosition[name]">
        <view v-if="actionFor(name)?.cards?.length" class="play-cards">
          <PlayingCard v-for="(card,index) in actionFor(name).cards" :key="`${name}-${index}`" :card="card" disabled />
        </view>
        <text v-else-if="actionFor(name)?.is_pass" class="pass-mark">PASS</text>
      </view>
      <view class="desk-center">
        <text class="desk-label">本轮牌桌</text>
        <text v-if="!tableActions.length" class="empty-desk">等待首出</text>
        <text class="last-play">{{ lastPlayerText }}</text>
      </view>
      <scroll-view v-if="tableActions.length" scroll-y class="played-history" :scroll-top="historyScrollTop">
        <view
          v-for="(action,index) in tableActions"
          :key="`action-${index}`"
          class="played-action"
          :class="{ latest: index === tableActions.length - 1 }"
        >
          <text class="action-player">{{ action.player }}</text>
          <view v-if="action.cards?.length" class="history-cards">
            <PlayingCard v-for="(card,cardIndex) in action.cards" :key="`${index}-${cardIndex}`" :card="card" disabled />
          </view>
          <text v-else class="history-pass">PASS</text>
        </view>
      </scroll-view>
      <view class="turn-pill">{{ turnText }}</view>
    </view>

    <view class="hand-panel">
      <view class="row-between"><text class="hand-title">我的手牌</text><text class="muted">已选 {{ store.selectedIndices.length }} 张</text></view>
      <scroll-view scroll-x class="hand-scroll">
        <view class="hand-row">
          <PlayingCard v-for="(card, index) in store.hand" :key="`${card}-${index}`" :card="card" :selected="store.selectedIndices.includes(index)" @select="store.toggleCard(index)" />
        </view>
      </scroll-view>
      <view class="actions">
        <u-button plain color="#d8b65b" text="AI推荐" @click="goRecommend" />
        <u-button plain color="#567064" text="PASS" :disabled="store.aiThinking" @click="pass" />
        <u-button type="primary" color="#0b5d3b" text="出牌" :loading="store.aiThinking" :disabled="store.aiThinking" @click="play" />
      </view>
      <u-button class="finish-link" type="primary" plain color="#0b5d3b" size="small" text="结束演示并查看结算" @click="finish" />
    </view>
  </view>
</template>

<script setup>
import { computed } from 'vue'
import { useGameStore } from '@/store/game'
import PlayingCard from '@/components/PlayingCard.vue'
const store = useGameStore()
const tableActions = computed(() => store.game?.state?.table_plays || [])
const historyScrollTop = computed(() => tableActions.value.length * 120)
const playerNames = ['你', 'AI-1', 'AI-2', 'AI-3']
const playPosition = { '你': 'bottom-play', 'AI-1': 'left-play', 'AI-2': 'top-play', 'AI-3': 'right-play' }
const actionFor = name => [...tableActions.value].reverse().find(action => action.player === name)
const lastPlayerText = computed(() => store.game?.state?.last_action_text || (store.game?.state?.last_player_name ? `${store.game.state.last_player_name} · 最近出牌` : '本轮由你开始'))
const turnText = computed(() => {
  if (store.game?.winner) return '牌局已结束'
  const index = store.game?.state?.current_player_index || 0
  return index === 0 ? '轮到你出牌' : `轮到 AI-${index}`
})
const playerCount = name => store.game?.players?.find(player => player.name === name)?.hand_count ?? 27
const back = () => uni.navigateBack()
const toast = title => uni.showToast({ title, icon: 'none' })
const play = async () => { try { await store.playSelected(); toast('出牌成功') } catch (error) { toast(error.message) } }
const pass = async () => { try { await store.pass(); toast('已过牌') } catch (error) { toast(error.message) } }
const goRecommend = () => uni.navigateTo({ url: '/pages/recommend/index' })
const finish = () => { store.finishDemo(); uni.navigateTo({ url: '/pages/settlement/index' }) }
</script>

<style scoped lang="scss">
.table-page { min-height: 100vh; background: #075337; color: #fff; }
.table-head { height: 104rpx; padding: 38rpx 28rpx 16rpx; display: flex; align-items: center; justify-content: space-between; font-weight: 700; }
.game-table { position: relative; height: 670rpx; margin: 0 18rpx; overflow: hidden; border: 2rpx solid rgba(216,182,91,.42); border-radius: 42rpx; background: radial-gradient(circle, #168257 0, #0e6b47 60%, #09553a 100%); box-shadow: inset 0 0 70rpx rgba(0,0,0,.2); }
.player { position: absolute; display: flex; flex-direction: column; align-items: center; gap: 4rpx; font-size: 23rpx; }.player.top { top: 24rpx; left: 50%; transform: translateX(-50%); }.player.left { left: 20rpx; top: 250rpx; }.player.right { right: 20rpx; top: 250rpx; }
.avatar { width: 72rpx; height: 72rpx; display: flex; align-items: center; justify-content: center; border: 3rpx solid rgba(255,255,255,.65); border-radius: 50%; background: #164d38; font-size: 23rpx; font-weight: 800; }.count { font-size: 20rpx; color: rgba(255,255,255,.65); }
.desk-center { position: absolute; left: 50%; top: 49%; transform: translate(-50%,-50%); text-align: center; }.desk-label,.last-play { display: block; font-size: 22rpx; color: rgba(255,255,255,.68); }.empty-desk { display:block; margin:18rpx 0; color:rgba(255,255,255,.55); font-size:25rpx; }
.table-play { position:absolute; z-index:2; min-width:90rpx; min-height:74rpx; display:flex; align-items:center; justify-content:center; }.top-play { top:120rpx; left:50%; transform:translateX(-50%); }.left-play { left:105rpx; top:285rpx; }.right-play { right:105rpx; top:285rpx; }.bottom-play { bottom:92rpx; left:50%; transform:translateX(-50%); }
.play-cards { display:flex; justify-content:center; }.play-cards :deep(.card) { width:54rpx; height:78rpx; flex-basis:54rpx; padding:6rpx; margin-left:-16rpx; border-radius:7rpx; }.play-cards :deep(.card:first-child) { margin-left:0; }.play-cards :deep(.card__label) { font-size:20rpx; }.play-cards :deep(.card__suit) { margin-top:4rpx; font-size:18rpx; }.pass-mark { padding:6rpx 12rpx; border-radius:10rpx; background:rgba(0,0,0,.2); color:rgba(255,255,255,.72); font-size:21rpx; font-weight:700; }
.played-history { position:absolute; z-index:3; left:50%; top:50%; width:330rpx; height:250rpx; transform:translate(-50%,-50%); padding:8rpx; border-radius:16rpx; background:rgba(4,54,35,.34); box-sizing:border-box; }.played-action { display:flex; align-items:center; min-height:50rpx; margin:5rpx 0; padding:5rpx 8rpx; border:2rpx solid transparent; border-radius:10rpx; opacity:.72; }.played-action.latest { border-color:#f4d66f; background:rgba(244,214,111,.15); box-shadow:0 0 16rpx rgba(244,214,111,.55); opacity:1; }.action-player { width:58rpx; flex:0 0 58rpx; color:#fff; font-size:18rpx; font-weight:700; }.history-cards { display:flex; min-width:0; }.history-cards :deep(.card) { width:42rpx; height:58rpx; flex-basis:42rpx; padding:4rpx; margin-left:-12rpx; border-radius:5rpx; }.history-cards :deep(.card:first-child) { margin-left:0; }.history-cards :deep(.card__label) { font-size:16rpx; }.history-cards :deep(.card__suit) { margin-top:2rpx; font-size:14rpx; }.played-action.latest .history-cards :deep(.card) { border-color:#f4d66f; box-shadow:0 0 10rpx rgba(244,214,111,.8); transform:translateY(-3rpx); }.history-pass { color:rgba(255,255,255,.7); font-size:18rpx; font-weight:700; }
.turn-pill { position: absolute; bottom: 28rpx; left: 50%; transform: translateX(-50%); padding: 10rpx 26rpx; border-radius: 99rpx; color: #3d3216; background: #e4c66d; font-size: 24rpx; font-weight: 700; }
.hand-panel { margin-top: -12rpx; padding: 28rpx 24rpx 22rpx; border-radius: 30rpx 30rpx 0 0; background: #f3f7f4; color: #18372a; }.hand-title { font-weight: 800; }
.hand-scroll { width: 100%; height: 164rpx; margin-top: 24rpx; }.hand-row { min-width: max-content; display: flex; gap: 7rpx; padding: 22rpx 4rpx; }
.actions { display: grid; grid-template-columns: 1fr 1fr 1.4fr; gap: 14rpx; }.finish-link { margin-top: 18rpx; }
@media screen and (min-width: 768px) {
  .table-page { max-width: 980px; margin: 0 auto; box-shadow: 0 0 50px rgba(5, 65, 42, .18); }
  .game-table { height: 610px; }
  .hand-panel { padding-left: 36px; padding-right: 36px; }
}
</style>
