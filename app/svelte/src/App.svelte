<script>
    import { onMount } from "svelte";
    import BotCard from "./BotCard.svelte";
    import Navigation from "./Navigation.svelte";
    
    let bots = {};
    let activePage = "home";
    let activeBot = null;
    let iframeURL = "";
    let loading = true;
    let error = null;
    
    onMount(async () => {
      try {
        const response = await fetch("/api/bots");
        if (!response.ok) {
          throw new Error(`HTTP error ${response.status}`);
        }
        bots = await response.json();
        
        // Check URL for bot selection
        const path = window.location.pathname;
        const botId = path.split("-chat")[0].replace("/", "");
        
        if (botId && bots[botId]) {
          navigateToBot(botId);
        }
      } catch (error) {
        console.error("Error loading bots:", error);
        error = "Failed to load bots. Please try again.";
      } finally {
        loading = false;
      }
    });
    
    function navigateToBot(botId) {
      activePage = "chat";
      activeBot = bots[botId];
      iframeURL = activeBot.chat_path;
      
      // Update URL
      window.history.pushState({}, "", `/${botId}-chat`);
    }
    
    function navigateHome() {
      activePage = "home";
      activeBot = null;
      iframeURL = "";
      window.history.pushState({}, "", "/");
    }
  </script>
  
  <div class="flex h-screen bg-background text-text-primary">
    <Navigation {bots} onNavClick={navigateToBot} onHomeClick={navigateHome} activePage={activePage} />
    
    <main class="ml-60 p-8 w-[calc(100%-240px)]">
      {#if loading}
        <div class="flex justify-center items-center h-[calc(100vh-100px)]">
          <div class="animate-pulse text-accent text-xl">Loading...</div>
        </div>
      {:else if error}
        <div class="bg-red-800 text-white p-4 rounded-lg">{error}</div>
      {:else if activePage === "home"}
        <div class="flex items-center gap-4 mb-12">
          <h1 class="text-3xl font-bold">Welcome to Ragnode</h1>
        </div>
        
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
          {#each Object.entries(bots) as [id, bot]}
            <BotCard 
              id={id} 
              title={bot.title} 
              description={bot.description}
              onClick={() => navigateToBot(id)}
            />
          {/each}
        </div>
      {:else if activePage === "chat" && activeBot}
        <div class="mb-8">
          <h1 class="text-2xl font-semibold">{activeBot.title}</h1>
          <p class="text-text-secondary mt-2">{activeBot.description}</p>
        </div>
        
        <div class="bg-surface rounded-lg border border-border h-[calc(100vh-200px)] overflow-hidden">
          <iframe src={iframeURL} class="w-full h-full" frameborder="0" title="Chat" loading="lazy" sandbox="allow-scripts allow-same-origin allow-forms"></iframe>
        </div>
      {/if}
    </main>
  </div>
  
  <style>
    :global(body) {
      margin: 0;
      font-family: system-ui, -apple-system, sans-serif;
      background: rgb(17, 17, 18);
      color: #f3f4f6;
      display: flex;
    }
  </style>