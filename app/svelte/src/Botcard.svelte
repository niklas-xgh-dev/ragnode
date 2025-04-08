<script>
    export let id;
    export let title;
    export let description;
    export let onClick;
  </script>
  
  <div 
    class="bg-surface border border-border rounded-lg p-6 cursor-pointer transition-all hover:translate-y-[-2px] hover:border-accent"
    on:click={onClick}
  >
    <h2 class="text-xl font-semibold mb-4 text-accent">{title}</h2>
    <p class="text-text-secondary">{description}</p>
  </div>