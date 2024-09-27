const { ref, computed } = Vue

app.component('context-form', {
  template: `
    <q-form @submit="onSubmit" class="context-form q-gutter-md">
      <q-select
        v-model="form.work_type"
        :options="workTypeOptions"
        label="Work Type"
        :rules="[val => !!val || 'Work type is required']"
      />

      <q-input
        v-model="form.genre"
        label="Genre"
        :rules="[val => !!val || 'Genre is required']"
      >
        <template v-slot:append>
          <q-icon name="help" color="primary">
            <q-tooltip>
              Enter the genre of your work (e.g., Science Fiction, Romance, Mystery)
            </q-tooltip>
          </q-icon>
        </template>
      </q-input>

      <q-select
        v-model="form.target_audience"
        :options="audienceOptions"
        label="Target Audience"
        :rules="[val => !!val || 'Target audience is required']"
      />

      <q-input
        v-model="form.time_period"
        label="Time Period"
        :rules="[val => !!val || 'Time period is required']"
      >
        <template v-slot:append>
          <q-icon name="help" color="primary">
            <q-tooltip>
              Enter the time period of your story (e.g., Victorian Era, 1980s, Near Future)
            </q-tooltip>
          </q-icon>
        </template>
      </q-input>

      <q-select
        v-model="form.primary_language"
        :options="languageOptions"
        label="Primary Language"
        :rules="[val => !!val || 'Primary language is required']"
      />

      <q-slider
        v-model="form.realism_level"
        :min="0"
        :max="4"
        :step="1"
        label
        label-always
        :marker-labels="realismLabels"
      />

      <q-input
        v-model="form.additional_context"
        type="textarea"
        label="Additional Context"
        hint="Any other relevant information about your story"
      />

      <div>
        <q-btn label="Submit" type="submit" color="primary"/>
        <q-btn label="Reset" type="reset" color="primary" flat class="q-ml-sm" @click="resetForm" />
      </div>
    </q-form>
  `,
  props: {
    storyId: {
      type: Number,
      required: true
    },
    storyTitle: {
      type: String,
      required: true
    },
    initialContext: {
      type: Object,
      default: () => ({})
    }
  },
  setup(props) {
    const form = ref({
      work_type: props.initialContext.work_type || '',
      genre: props.initialContext.genre || '',
      target_audience: props.initialContext.target_audience || '',
      time_period: props.initialContext.time_period || '',
      primary_language: props.initialContext.primary_language || '',
      realism_level: props.initialContext.realism_level || 2,
      additional_context: props.initialContext.additional_context || ''
    })

    const workTypeOptions = [
      'Novel', 'Short Story', 'Screenplay', 'Stage Play'
    ]

    const audienceOptions = [
      'Children', 'Young Adult', 'Adult', 'All Ages'
    ]

    const languageOptions = [
      'English', 'Spanish', 'French', 'German', 'Chinese', 'Japanese', 'Other'
    ]

    const realismLabels = {
      0: 'Fantasy',
      1: 'Magical Realism',
      2: 'Realistic Fiction',
      3: 'Historical Fiction',
      4: 'Non-Fiction'
    }

    const onSubmit = () => {
      console.log('Form submitted:', form.value)
      // Here you would typically send the form data to your server
      // You can add an API call here to send the data to your Flask backend
    }

    const resetForm = () => {
      Object.assign(form.value, props.initialContext)
    }

    return {
      form,
      workTypeOptions,
      audienceOptions,
      languageOptions,
      realismLabels,
      onSubmit,
      resetForm
    }
  }
})
