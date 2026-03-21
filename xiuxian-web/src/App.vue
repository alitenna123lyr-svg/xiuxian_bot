<script setup lang="ts">
import NavBar from '@/components/NavBar.vue'
</script>

<template>
  <router-view v-slot="{ Component }">
    <Transition name="page" mode="out-in">
      <component :is="Component" />
    </Transition>
  </router-view>
  <NavBar />
</template>
