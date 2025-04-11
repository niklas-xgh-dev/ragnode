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
    let isDev = window.location.port === "3000";
    
    // Function to generate API URLs properly whether in dev or prod
    function getApiUrl(path) {
      if (isDev) {
        return `/api${path}`;
      } else {
        return `/api${path}`;
      }
    }
    
    onMount(async () => {
      try {
        console.log("Environment:", isDev ? "Development" : "Production");
        const response = await fetch(getApiUrl("/bots"));
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
      } catch (err) {
        console.error("Error loading bots:", err);
        error = "Failed to load bots. Please try again.";
      } finally {
        loading = false;
      }
    });
    
    function navigateToBot(botId) {
      activePage = "chat";
      activeBot = bots[botId];
      
      // Handle the chat path for the iframe
      // If in dev mode and running in different containers, use the right URL
      const isDev = window.location.port === "3000";
      const baseUrl = isDev ? "http://localhost:8000" : "";
      iframeURL = `${baseUrl}${activeBot.chat_path}`;
      console.log("Navigating to bot:", botId, "URL:", iframeURL);
      
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
  
  <div class="flex min-h-screen bg-background text-text-primary">
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
        <div>
          <div class="mb-8 flex justify-between items-center">
            <div>
              <h1 class="text-2xl font-semibold">{activeBot.title}</h1>
              <p class="text-text-secondary mt-2">{activeBot.description}</p>
            </div>
            <button 
              class="px-4 py-2 bg-accent text-white rounded hover:bg-accent/80 transition-colors"
              on:click={navigateHome}
            >
              Back to Home
            </button>
          </div>
          
          <div class="bg-surface rounded-lg border border-border h-[calc(100vh-200px)] overflow-hidden">
            <iframe 
              src={iframeURL} 
              class="w-full h-full" 
              frameborder="0" 
              title="Chat" 
              loading="lazy" 
              allow="camera; microphone"
              referrerpolicy="no-referrer"
              sandbox="allow-scripts allow-same-origin allow-forms allow-popups allow-modals allow-top-navigation">
            </iframe>
          </div>
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