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
      <view class="desk-center">
        <text class="desk-label">当前牌面</text>
        <view v-if="tableCards.length" class="played"><PlayingCard v-for="(card,index) in tableCards" :key="index" :card="card" disabled /></view>
        <text v-else class="empty-desk">等待首出</text>
        <text class="last-play">{{ lastPlayerText }}</text>
      </view>
      <view class="turn-pill">{{ store.game?.winner ? '牌局已结束' : '轮到你出牌' }}</view>
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
        <u-button plain color="#567064" text="PASS" @click="pass" />
        <u-button type="primary" color="#0b5d3b" text="出牌" @click="play" />
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
const tableCards = computed(() => store.game?.state?.last_played_cards || [])
const lastPlayerText = computed(() => store.game?.state?.last_player_name ? `${store.game.state.last_player_name} · 最近出牌` : '本轮由你开始')
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
.desk-center { position: absolute; left: 50%; top: 47%; transform: translate(-50%,-50%); text-align: center; }.desk-label,.last-play { display: block; font-size: 22rpx; color: rgba(255,255,255,.68); }.played { max-width:360rpx; display: flex; justify-content: center; gap: 6rpx; margin: 16rpx 0; }.empty-desk { display:block; margin:38rpx 0; color:rgba(255,255,255,.55); font-size:25rpx; }
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
