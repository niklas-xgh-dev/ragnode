<script>
    export let bots = {};
    export let onNavClick;
    export let onHomeClick;
    export let activePage = "home";
  </script>
  
  <nav class="w-60 h-screen fixed bg-surface p-8 pb-0 border-r border-border">
    <div class="flex justify-center w-full mb-8">
      <img src="/static/logo_v2.svg" alt="Ragnode Logo" class="w-24 h-auto">
    </div>
    
    <ul class="list-none p-0 m-0">
      <li>
        <button 
          class="block w-full text-left py-3 px-8 text-text-primary no-underline transition-colors duration-200
            hover:bg-nav-hover
            {activePage === 'home' ? 'bg-nav-active border-r-3 border-accent' : ''}"
          on:click={onHomeClick}
        >
          Home
        </button>
      </li>
      
      {#each Object.entries(bots) as [id, bot]}
        <li>
          <button 
            class="block w-full text-left py-3 px-8 text-text-primary no-underline transition-colors duration-200
              hover:bg-nav-hover
              {activePage === 'chat' && bot.id === id ? 'bg-nav-active border-r-3 border-accent' : ''}"
            on:click={() => onNavClick(id)}
          >
            {bot.title}
          </button>
        </li>
      {/each}
    </ul>
  </nav>