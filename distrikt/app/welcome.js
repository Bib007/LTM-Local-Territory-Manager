'use strict';
// A single setup guide. Older entry points delegate to the same questions.
const Welcome={
 language(){return I18n.language();},
 auto(){const setup=state.settings?.onboarding;if(setup?.completed)return;if(setup?.version===2){Onboarding.open(4);return;}if(state.cards.length||state.publishers.length||state.loans.length)return;try{if(localStorage.getItem('ltm-welcome-seen'))return;}catch{}Onboarding.open();},
 open(step=0){Onboarding.open(step);}
};
document.addEventListener('click',e=>{if(!e.target.closest('[data-welcome="open"]'))return;e.preventDefault();Onboarding.open();});
